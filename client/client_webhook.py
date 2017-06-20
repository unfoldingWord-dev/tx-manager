from __future__ import print_function, unicode_literals
import urllib
import copy
import os
import tempfile
import requests
import logging
import json
from datetime import datetime
from general_tools import file_utils
from general_tools.file_utils import unzip, get_subdirs, write_file, add_contents_to_zip, add_file_to_zip
from general_tools.url_utils import download_file
from resource_container.ResourceContainer import RC
from client.preprocessors import do_preprocess
from aws_tools.s3_handler import S3Handler


class ClientWebhook(object):

    def __init__(self, commit_data=None, api_url=None, pre_convert_bucket=None, cdn_bucket=None,
                 gogs_url=None, gogs_user_token=None):
        """
        :param dict commit_data:
        :param string api_url:
        :param string pre_convert_bucket:
        :param string cdn_bucket:
        :param string gogs_url:
        :param string gogs_user_token:
        """
        self.commit_data = commit_data
        self.api_url = api_url
        self.pre_convert_bucket = pre_convert_bucket
        self.cdn_bucket = cdn_bucket
        self.gogs_url = gogs_url
        self.gogs_user_token = gogs_user_token
        self.logger = logging.getLogger()

        if self.pre_convert_bucket:
            # we use us-west-2 for our s3 buckets
            self.source_url_base = 'https://s3-us-west-2.amazonaws.com/{0}'.format(self.pre_convert_bucket)
        else:
            self.source_url_base = None

        self.cdn_handler = None
        self.preconvert_handler = None

        # move everything down one directory levek for simple delete
        self.intermediate_dir = 'tx-manager'
        self.base_temp_dir = os.path.join(tempfile.gettempdir(), self.intermediate_dir)

    def process_webhook(self):
        try:
            os.makedirs(self.base_temp_dir)
        except:
            pass

        commit_id = self.commit_data['after']
        commit = None
        for commit in self.commit_data['commits']:
            if commit['id'] == commit_id:
                break
        commit_id = commit_id[:10]  # Only use the short form

        commit_url = commit['url']
        commit_message = commit['message']

        if self.gogs_url not in commit_url:
            raise Exception('Repos can only belong to {0} to use this webhook client.'.format(self.gogs_url))

        repo_name = self.commit_data['repository']['name']
        repo_owner = self.commit_data['repository']['owner']['username']
        compare_url = self.commit_data['compare_url']

        if 'pusher' in self.commit_data:
            pusher = self.commit_data['pusher']
        else:
            pusher = {'username': commit['author']['username']}
        pusher_username = pusher['username']

        if not self.cdn_handler:
            self.cdn_handler = S3Handler(self.cdn_bucket)

        if not self.preconvert_handler:
            self.preconvert_handler = S3Handler(self.pre_convert_bucket)

        # 1) Download and unzip the repo files
        repo_dir = self.get_repo_files(commit_url, repo_name)

        # Get the resource container
        rc = RC(repo_dir, repo_name)

        # Preprocess the files
        output_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='output_')
        results, preprocessor = do_preprocess(rc, repo_dir, output_dir)

        # 3) Zip up the massaged files
        # commit_id is a unique ID for this lambda call, so using it to not conflict with other requests
        zip_filepath = tempfile.mktemp(dir=self.base_temp_dir, suffix='.zip')
        self.logger.debug('Zipping files from {0} to {1}...'.format(output_dir, zip_filepath))
        add_contents_to_zip(zip_filepath, output_dir)
        self.logger.debug('finished.')

        # 4) Upload zipped file to the S3 bucket
        file_key = self.upload_zip_file(commit_id, zip_filepath)

        if not preprocessor.isMultipleJobs():
            # Send job request to tx-manager
            identifier, job = self.send_job_request_to_tx_manager(commit_id, file_key, rc, repo_name, repo_owner)

            s3_commit_key = 'u/{0}'.format(identifier)
            self.clear_commit_directory_in_cdn(s3_commit_key)

            # Download the project.json file for this repo (create it if doesn't exist) and update it
            self.update_project_json(commit_id, job, repo_name, repo_owner)

            # Compile data for build_log.json
            build_log_json = self.create_build_log(commit_id, commit_message, commit_url, compare_url, job,
                                                   pusher_username, repo_name, repo_owner)

            # Upload build_log.json to S3:
            self.upload_build_log_to_s3(build_log_json, s3_commit_key)
            file_utils.remove_tree(self.base_temp_dir)  # cleanup
            if len(job['errors']) > 0:
                raise Exception('; '.join(job['errors']))
            else:
                return build_log_json

        # -------------------------
        # multiple book project
        # -------------------------

        books = preprocessor.getBookList()
        self.logger.debug('Splitting job into separate parts for books: ' + ','.join(books))
        errors = []
        build_logs = []
        jobs = []

        master_identifier = self.create_new_job_id(repo_owner, repo_name, commit_id)
        master_s3_commit_key = 'u/{0}'.format(master_identifier)
        self.clear_commit_directory_in_cdn(master_s3_commit_key)

        book_count = len(books)
        last_job_id = 0
        for i in range(0, book_count):
            book = books[i]
            part_id = '{0}_of_{1}'.format(i, book_count)

            # 3) Zip up the massaged files for just the one book

            self.logger.debug('Adding job for {0} part {1}'.format(book, part_id))

            # Send job request to tx-manager
            source_url = self.build_multipart_source(file_key, book)
            identifier, job = self.send_job_request_to_tx_manager(commit_id, source_url, rc, repo_name, repo_owner,
                                                                  count=book_count, part=i, book=book)
            jobs.append(job)
            last_job_id = job['job_id']

            build_log_json = self.create_build_log(commit_id, commit_message, commit_url, compare_url, job,
                                                   pusher_username, repo_name, repo_owner)

            if len(book) > 0:
                build_log_json['book'] = book

            # Upload build_log.json to S3:
            self.upload_build_log_to_s3(build_log_json, master_s3_commit_key, str(i) + "_")

            errors += job['errors']
            build_logs.append(build_log_json)

        # Download the project.json file for this repo (create it if doesn't exist) and update it
        self.update_project_json(commit_id, jobs[0], repo_name, repo_owner)

        source_url = self.source_url_base + "/preconvert/" + commit_id + '.zip'
        build_logs_json = copy.copy(build_log_json)
        build_logs_json['multiple'] = True
        build_logs_json['build_logs'] = build_logs
        build_logs_json['job_id'] = last_job_id
        build_logs_json['source'] = source_url
        errors = []
        for i in range(0, book_count):
            build_log = build_logs[i]
            errors += build_log['errors']
        build_logs_json['errors'] = errors

        # Upload build_log.json to S3:
        self.upload_build_log_to_s3(build_logs_json, master_s3_commit_key)
        file_utils.remove_tree(self.base_temp_dir)  # cleanup
        if len(errors) > 0:
            raise Exception('; '.join(errors))
        else:
            return build_logs_json

    def build_multipart_source(self, file_key, book):
        params = urllib.urlencode({'convert_only': book})
        source_url = '{0}?{1}'.format(file_key, params)
        return source_url

    def clear_commit_directory_in_cdn(self, s3_commit_key):
        # clear out the commit directory in the cdn bucket for this project revision
        for obj in self.cdn_handler.get_objects(prefix=s3_commit_key):
            self.logger.debug('Removing file: ' + obj.key)
            self.cdn_handler.delete_file(obj.key)

    def upload_build_log_to_s3(self, build_log_json, s3_commit_key, part=''):
        build_log_file = os.path.join(self.base_temp_dir, 'build_log.json')
        write_file(build_log_file, build_log_json)
        upload_key = '{0}/{1}build_log.json'.format(s3_commit_key, part)
        self.logger.debug('Saving build log to ' + upload_key)
        self.cdn_handler.upload_file(build_log_file, upload_key)
        # self.logger.debug('build log contains: ' + json.dumps(build_log_json))

    def create_build_log(self, commit_id, commit_message, commit_url, compare_url, job, pusher_username, repo_name,
                         repo_owner):
        build_log_json = job
        build_log_json['repo_name'] = repo_name
        build_log_json['repo_owner'] = repo_owner
        build_log_json['commit_id'] = commit_id
        build_log_json['committed_by'] = pusher_username
        build_log_json['commit_url'] = commit_url
        build_log_json['compare_url'] = compare_url
        build_log_json['commit_message'] = commit_message
        return build_log_json

    def update_project_json(self, commit_id, job, repo_name, repo_owner):
        project_json_key = 'u/{0}/{1}/project.json'.format(repo_owner, repo_name)
        project_json = self.cdn_handler.get_json(project_json_key)
        project_json['user'] = repo_owner
        project_json['repo'] = repo_name
        project_json['repo_url'] = 'https://git.door43.org/{0}/{1}'.format(repo_owner, repo_name)
        commit = {
            'id': commit_id,
            'created_at': job['created_at'],
            'status': job['status'],
            'success': job['success'],
            'started_at': None,
            'ended_at': None
        }
        if 'commits' not in project_json:
            project_json['commits'] = []
        commits = []
        for c in project_json['commits']:
            if c['id'] != commit_id:
                commits.append(c)
        commits.append(commit)
        project_json['commits'] = commits
        project_file = os.path.join(self.base_temp_dir, 'project.json')
        write_file(project_file, project_json)
        self.cdn_handler.upload_file(project_file, project_json_key)

    def upload_zip_file(self, commit_id, zip_filepath):
        file_key = 'preconvert/{0}.zip'.format(commit_id)
        self.logger.debug('Uploading {0} to {1}/{2}...'.format(zip_filepath, self.pre_convert_bucket, file_key))
        try:
            self.preconvert_handler.upload_file(zip_filepath, file_key)
        except Exception as e:
            self.logger.error('Failed to upload zipped repo up to server')
            self.logger.exception(e)
        finally:
            self.logger.debug('finished.')

        return file_key

    def get_repo_files(self, commit_url, repo_name):
        temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='{0}_'.format(repo_name))
        self.download_repo(commit_url, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name.lower())
        if not os.path.isdir(repo_dir):
            repo_dir = temp_dir

        return repo_dir

    def send_job_request_to_tx_manager(self, commit_id, file_key, rc, repo_name, repo_owner,
                                       count=0, part=0, book=None):
        source_url = self.source_url_base + "/" + file_key
        callback_url = self.api_url + '/client/callback'
        tx_manager_job_url = self.api_url + '/tx/job'

        identifier = self.create_new_job_id(repo_owner, repo_name, commit_id, count, part, book)

        payload = {
            "identifier": identifier,
            "gogs_user_token": self.gogs_user_token,
            "resource_type": rc.resource.identifier,
            "input_format": rc.resource.file_ext,
            "output_format": "html",
            "source": source_url,
            "callback": callback_url
        }
        return self.add_payload_to_tx_converter(callback_url, identifier, payload, rc, source_url, tx_manager_job_url)

    def create_new_job_id(self, repo_owner, repo_name, commit_id, count=0, part=0, book=None):
        if not count:
            identifier = "{0}/{1}/{2}".format(repo_owner, repo_name,
                                              commit_id)  # The way to know which repo/commit goes to this job request
        else:  # if this is part of a multipart job
            # The way to know which repo/commit goes to this job request
            identifier = "{0}/{1}/{2}/{3}/{4}/{5}".format(repo_owner, repo_name, commit_id, count, part, book)
        return identifier

    def add_payload_to_tx_converter(self, callback_url, identifier, payload, rc, source_url, tx_manager_job_url):
        headers = {"content-type": "application/json"}
        self.logger.debug('Making request to tX-Manager URL {0} with payload:'.format(tx_manager_job_url))
        # remove token from printout, so it will not show in integration testing logs on Travis, etc.
        log_payload = payload.copy()
        log_payload["gogs_user_token"] = "DUMMY"
        self.logger.debug(log_payload)
        response = requests.post(tx_manager_job_url, json=payload, headers=headers)
        self.logger.debug('finished.')
        # Fake job in case tx-manager returns an error, can still build the build_log.json
        job = {
            'job_id': None,
            'identifier': identifier,
            'resource_type': rc.resource.identifier,
            'input_format': rc.resource.file_ext,
            'output_format': 'html',
            'source': source_url,
            'callback': callback_url,
            'message': 'Conversion started...',
            'status': 'requested',
            'success': None,
            'created_at': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'log': [],
            'warnings': [],
            'errors': []
        }
        if response.status_code != requests.codes.ok:
            job['status'] = 'failed'
            job['success'] = False
            job['message'] = 'Failed to convert'

            if response.text:
                # noinspection PyBroadException
                try:
                    json_data = json.loads(response.text)
                    if 'errorMessage' in json_data:
                        error = json_data['errorMessage']
                        if error.startswith('Bad Request: '):
                            error = error[len('Bad Request: '):]

                        job['errors'].append(error)
                except:
                    pass
        else:
            json_data = json.loads(response.text)

            if 'job' not in json_data:
                job['status'] = 'failed'
                job['success'] = False
                job['message'] = 'Failed to convert'
                job['errors'].append('tX Manager did not return any info about the job request.')
            else:
                job = json_data['job']
        return identifier, job

    def download_repo(self, commit_url, repo_dir):
        """
        Downloads and unzips a git repository from Github or git.door43.org

        :param str|unicode commit_url: The URL of the repository to download
        :param str|unicode repo_dir:   The directory where the downloaded file should be unzipped
        :return: None
        """
        repo_zip_url = commit_url.replace('commit', 'archive') + '.zip'
        repo_zip_file = os.path.join(self.base_temp_dir, repo_zip_url.rpartition('/')[2])

        try:
            self.logger.debug('Downloading {0}...'.format(repo_zip_url))

            # if the file already exists, remove it, we want a fresh copy
            if os.path.isfile(repo_zip_file):
                os.remove(repo_zip_file)

            download_file(repo_zip_url, repo_zip_file)
        finally:
            self.logger.debug('finished.')

        try:
            self.logger.debug('Unzipping {0}...'.format(repo_zip_file))
            unzip(repo_zip_file, repo_dir)
        finally:
            self.logger.debug('finished.')

        # clean up the downloaded zip file
        if os.path.isfile(repo_zip_file):
            os.remove(repo_zip_file)
