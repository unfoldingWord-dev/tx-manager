from __future__ import print_function, unicode_literals
import os
import sys
import tempfile
import requests
import logging
import json
import shutil
from logging import Logger
from datetime import datetime
from general_tools.file_utils import unzip, get_subdirs, write_file, add_contents_to_zip, add_file_to_zip
from general_tools.url_utils import download_file
from door43_tools import preprocessors
from door43_tools.manifest_handler import Manifest, MetaData
from aws_tools.s3_handler import S3Handler


class ClientWebhook(object):

    def __init__(self, commit_data=None, api_url=None, pre_convert_bucket=None, cdn_bucket=None,
                 gogs_url=None, gogs_user_token=None, logger=None, s3_handler_class=S3Handler):
        """
        :param dict commit_data:
        :param string api_url:
        :param string pre_convert_bucket:
        :param string cdn_bucket:
        :param string gogs_url:
        :param string gogs_user_token:
        :param Logger logger:
        :param class s3_handler_class:
        """

        if not logger:
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger

        self.commit_data = commit_data
        self.api_url = api_url
        self.pre_convert_bucket = pre_convert_bucket
        self.cdn_bucket = cdn_bucket
        self.gogs_url = gogs_url
        self.gogs_user_token = gogs_user_token
        self.s3_handler_class = s3_handler_class

        if self.pre_convert_bucket:
            # we use us-west-2 for our s3 buckets
            self.source_url_base = 'https://s3-us-west-2.amazonaws.com/{0}'.format(self.pre_convert_bucket)
        else:
            self.source_url_base = None

        # move everything down one directory levek for simple delete
        self.intermediate_dir =  'tx-manager'
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

        # 1) Download and unzip the repo files
        temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='repo_')
        self.download_repo(commit_url, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = temp_dir

        # 2) Get the manifest file or make one if it doesn't exist based on meta.json, repo_name and file extensions
        manifest_path = os.path.join(repo_dir, 'manifest.json')
        if not os.path.isfile(manifest_path):
            manifest_path = os.path.join(repo_dir, 'project.json')
            if not os.path.isfile(manifest_path):
                manifest_path = None
        meta_path = os.path.join(repo_dir, 'meta.json')
        meta = None
        if os.path.isfile(meta_path):
            meta = MetaData(meta_path)
        manifest = Manifest(file_name=manifest_path, repo_name=repo_name, files_path=repo_dir, meta=meta)

        # determining how the repo was generated/created:
        generator = ''
        if manifest.generator and manifest.generator['name'] and manifest.generator['name'].startswith('ts'):
            generator = 'ts'
        if not generator:
            dirs = sorted(get_subdirs(repo_dir, True))
            if 'content' in dirs:
                repo_dir = os.path.join(repo_dir, 'content')
            elif 'usfm' in dirs:
                repo_dir = os.path.join(repo_dir, 'usfm')

        manifest_path = os.path.join(repo_dir, 'manifest.json')
        write_file(manifest_path, manifest.__dict__)  # Write it back out so it's using the latest manifest format

        input_format = manifest.format
        resource_type = manifest.resource['id']
        if resource_type == 'ulb' or resource_type == 'udb':
            resource_type = 'bible'

        try:
            preprocessor_class = self.str_to_class(
                'preprocessors.{0}{1}{2}Preprocessor'.format(generator.capitalize(),
                                                             resource_type.capitalize(),
                                                             input_format.capitalize()))
        except AttributeError as e:
            self.logger.info('Got AttributeError: {0}'.format(e.message))
            preprocessor_class = preprocessors.Preprocessor

        # merge the source files with the template
        output_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='output_')
        preprocessor = preprocessor_class(manifest, repo_dir, output_dir)
        preprocessor.run()

        # 3) Zip up the massaged files
        # context.aws_request_id is a unique ID for this lambda call, so using it to not conflict with other requests
        zip_filename = commit_id + '.zip'
        zip_filepath = os.path.join(self.base_temp_dir, zip_filename)
        self.logger.info('Zipping files from {0} to {1}...'.format(output_dir, zip_filepath))
        add_contents_to_zip(zip_filepath, output_dir)
        if os.path.isfile(manifest_path) and not os.path.isfile(os.path.join(output_dir, 'manifest.json')):
            add_file_to_zip(zip_filepath, manifest_path, 'manifest.json')
        self.logger.info('finished.')

        # 4) Upload zipped file to the S3 bucket
        s3_handler = self.s3_handler_class(self.pre_convert_bucket)
        file_key = "preconvert/" + zip_filename
        self.logger.info('Uploading {0} to {1}/{2}...'.format(zip_filepath, self.pre_convert_bucket, file_key))
        try:
            s3_handler.upload_file(zip_filepath, file_key)
        except Exception as e:
            self.logger.error('Failed to upload zipped repo up to server')
            self.logger.exception(e)
        finally:
            self.logger.info('finished.')

        # Send job request to tx-manager
        source_url = self.source_url_base+"/"+file_key
        callback_url = self.api_url + '/client/callback'
        tx_manager_job_url = self.api_url + '/tx/job'
        identifier = "{0}/{1}/{2}".format(repo_owner, repo_name,
                                          commit_id)  # The way to know which repo/commit goes to this job request
        if input_format == 'markdown':
            input_format = 'md'
        payload = {
            "identifier": identifier,
            "gogs_user_token": self.gogs_user_token,
            "resource_type": manifest.resource['id'],
            "input_format": input_format,
            "output_format": "html",
            "source": source_url,
            "callback": callback_url
        }

        headers = {"content-type": "application/json"}

        print('Making request to tx-Manager URL {0} with payload:'.format(tx_manager_job_url), end=' ')
        print(payload)
        response = requests.post(tx_manager_job_url, json=payload, headers=headers)
        print('finished.')

        # Fake job in case tx-manager returns an error, can still build the build_log.json
        job = {
            'job_id': None,
            'identifier': identifier,
            'resource_type': manifest.resource['id'],
            'input_format': input_format,
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
            job['message'] = 'Failed to convert!'

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

        cdn_handler = self.s3_handler_class(self.cdn_bucket)

        # Download the project.json file for this repo (create it if doesn't exist) and update it
        project_json_key = 'u/{0}/{1}/project.json'.format(repo_owner, repo_name)
        project_json = cdn_handler.get_json(project_json_key)
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
        cdn_handler.upload_file(project_file, project_json_key, 0)

        # Compile data for build_log.json
        build_log_json = job
        build_log_json['repo_name'] = repo_name
        build_log_json['repo_owner'] = repo_owner
        build_log_json['commit_id'] = commit_id
        build_log_json['committed_by'] = pusher_username
        build_log_json['commit_url'] = commit_url
        build_log_json['compare_url'] = compare_url
        build_log_json['commit_message'] = commit_message

        # Upload build_log.json and manifest.json to S3:
        s3_commit_key = 'u/{0}'.format(identifier)
        for obj in cdn_handler.get_objects(prefix=s3_commit_key):
            cdn_handler.delete_file(obj.key)
        build_log_file = os.path.join(self.base_temp_dir, 'build_log.json')
        write_file(build_log_file, build_log_json)
        cdn_handler.upload_file(build_log_file, s3_commit_key + '/build_log.json', 0)

        cdn_handler.upload_file(manifest_path, s3_commit_key + '/manifest.json', 0)

        if len(job['errors']) > 0:
            raise Exception('; '.join(job['errors']))
        else:
            return build_log_json

    @staticmethod
    def str_to_class(class_name_string):
        """
        Gets a class from a string.
        :param str|unicode class_name_string: The string of the class name
        """
        return reduce(getattr, class_name_string.split("."), sys.modules[__name__])

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
            self.logger.info('Downloading {0}...'.format(repo_zip_url))

            # if the file already exists, remove it, we want a fresh copy
            if os.path.isfile(repo_zip_file):
                os.remove(repo_zip_file)

            download_file(repo_zip_url, repo_zip_file)
        finally:
            self.logger.info('finished.')

        try:
            self.logger.info('Unzipping {0}...'.format(repo_zip_file))
            unzip(repo_zip_file, repo_dir)
        finally:
            self.logger.info('finished.')

        # clean up the downloaded zip file
        if os.path.isfile(repo_zip_file):
            os.remove(repo_zip_file)
