from __future__ import print_function, unicode_literals
import json
import os
import tempfile
import logging
from libraries.general_tools.file_utils import unzip, write_file, remove_tree, remove
from libraries.general_tools.url_utils import download_file
from libraries.aws_tools.s3_handler import S3Handler
from libraries.models.job import TxJob


class ClientCallback(object):

    def __init__(self, job_data=None, cdn_bucket=None, gogs_url=None):
        """
        :param dict job_data:
        :param string cdn_bucket:
        :param string gogs_url:
        """
        self.logger = logging.getLogger()
        self.job = TxJob(job_data)
        self.cdn_bucket = cdn_bucket
        self.gogs_url = gogs_url
        self.temp_dir = tempfile.mkdtemp(suffix="", prefix="client_callback_")
        self.cdn_handler = None

    def process_callback(self):
        if not self.cdn_handler:
            self.cdn_handler = S3Handler(self.cdn_bucket)

        parts = self.job.identifier.split('/')
        multiple_project = len(parts) >= 6
        part_count = '0'
        part_id = '0'
        if not multiple_project:
            owner_name, repo_name, commit_id = parts[0:3]  # extract fields
        else:
            owner_name, repo_name, commit_id, part_count, part_id, book = parts   # extract fields
            self.logger.debug('Multiple project, part {0} of {1}, converting book {2}'
                              .format(part_id, part_count, book))

        # The identifier is how to know which username/repo/commit this callback goes to
        s3_commit_key = 'u/{0}/{1}/{2}'.format(owner_name, repo_name, commit_id)
        upload_key = s3_commit_key
        if multiple_project:
            upload_key += "/" + part_id

        self.logger.debug('Callback for commit {0}...'.format(s3_commit_key))

        # Download the ZIP file of the converted files
        converted_zip_url = self.job.output
        converted_zip_file = os.path.join(self.temp_dir, converted_zip_url.rpartition('/')[2])
        remove(converted_zip_file)  # make sure old file not present
        download_success = True
        self.logger.debug('Downloading converted zip file from {0}...'.format(converted_zip_url))
        try:
            download_file(converted_zip_url, converted_zip_file)
        except:
            download_success = False  # if multiple project we note fail and move on
            if not multiple_project:
                remove_tree(self.temp_dir)  # cleanup
            if self.job.errors is None:
                self.job.errors = []
                self.job.errors.append("Missing converted file: " + converted_zip_url)
        finally:
            self.logger.debug('download finished, success={0}'.format(str(download_success)))

        if download_success:
            # Unzip the archive
            unzip_dir = self.unzip_converted_files(converted_zip_file)

            # Upload all files to the cdn_bucket with the key of <user>/<repo_name>/<commit> of the repo
            self.upload_converted_files(upload_key, unzip_dir)

        if multiple_project:
            # Now download the existing build_log.json file, update it and upload it back to S3
            build_log_json = self.update_build_log(s3_commit_key, part_id + "/")

            # mark part as finished
            self.cdn_upload_contents({}, s3_commit_key + '/' + part_id + '/finished')

            # check if all parts are present, if not return
            missing_parts = []
            finished_parts = self.cdn_handler.get_objects(prefix=s3_commit_key, suffix='/finished')
            finished_parts_file_names = ','.join([finished_parts[x].key for x in range(len(finished_parts))])
            self.logger.debug('found finished files: ' + finished_parts_file_names)

            count = int(part_count)
            for i in range(0, count):
                file_name = '{0}/finished'.format(i)

                match_found = False
                for part in finished_parts:
                    if file_name in part.key:
                        match_found = True
                        self.logger.debug('Found converted part: ' + part.key)
                        break

                if not match_found:
                    missing_parts.append(file_name)

            if len(missing_parts) > 0:
                # build_log_json = self.merge_build_logs(s3_commit_key, count)
                self.logger.debug('Finished processing part. Other parts not yet completed: ' + ','.join(missing_parts))
                remove_tree(self.temp_dir)  # cleanup
                return build_log_json

            self.logger.debug('All parts finished. Merging.')

            # all parts are present

            build_log_json = self.merge_build_logs(s3_commit_key, count)
            self.logger.debug('Updated build_log.json: ' + json.dumps(build_log_json))

            # Download the project.json file for this repo (create it if doesn't exist) and update it
            project_json = self.update_project_file(commit_id, owner_name, repo_name)
            self.logger.debug('Updated project.json: ' + json.dumps(project_json))

            self.logger.debug('Multiple parts: Finished deploying to cdn_bucket. Done.')
            remove_tree(self.temp_dir)  # cleanup
            return build_log_json

        else:  # single part conversion
            # Download the project.json file for this repo (create it if doesn't exist) and update it
            self.update_project_file(commit_id, owner_name, repo_name)

            # Now download the existing build_log.json file, update it and upload it back to S3
            build_log_json = self.update_build_log(s3_commit_key)

            self.logger.debug('Finished deploying to cdn_bucket. Done.')
            remove_tree(self.temp_dir)  # cleanup
            return build_log_json

    def merge_build_logs(self, s3_commit_key, count):
        master_build_log_json = self.get_build_log(s3_commit_key)
        build_logs_json = []
        self.job.status = 'success'
        self.job.log = []
        self.job.warnings = []
        self.job.errors = []
        for i in range(0, count):
            # self.logger.debug('Merging part {0}'.format(i))

            # Now download the existing build_log.json file
            part = str(i) + "/"
            build_log_json = self.get_build_log(s3_commit_key, part)

            self.build_log_sanity_check(build_log_json)

            build_logs_json.append(build_log_json)

            if 'book' in build_log_json:
                book = build_log_json['book']
            elif 'commit_id' in build_log_json:
                book = build_log_json['commit_id']  # if no book then use commit_id
            else:
                book = 'part_' + str(i)  # generate dummy name

            # merge build_log data
            self.job.log += self.prefix_list(build_log_json, 'log', book)
            self.job.errors += self.prefix_list(build_log_json, 'errors', book)
            self.job.warnings += self.prefix_list(build_log_json, 'warnings', book)
            if ('status' in build_log_json) and (build_log_json['status'] != 'success'):
                self.job.status = build_log_json['status']
            if ('success' in build_log_json) and (build_log_json['success'] is not None):
                self.job.success = build_log_json['success']
            if ('message' in build_log_json) and (build_log_json['message'] is not None):
                self.job.message = build_log_json['message']

        # Now upload the merged build_log.json file, update it and upload it back to S3
        master_build_log_json['build_logs'] = build_logs_json  # add record of all the parts
        build_logs_json0 = build_logs_json[0]
        master_build_log_json['commit_id'] = build_logs_json0['commit_id']
        master_build_log_json['created_at'] = build_logs_json0['created_at']
        master_build_log_json['started_at'] = build_logs_json0['started_at']
        master_build_log_json['repo_owner'] = build_logs_json0['repo_owner']
        master_build_log_json['repo_name'] = build_logs_json0['repo_name']
        master_build_log_json['resource_type'] = build_logs_json0['resource_type']
        build_log_json = self.upload_build_log(master_build_log_json, s3_commit_key)
        return build_log_json

    def prefix_list(self, build_log_json, key, book):
        if key not in build_log_json:
            return []

        items = build_log_json[key]
        for i in range(0, len(items)):
            item = items[i]
            new_text = book + ': ' + item
            items[i] = new_text
        return items

    def build_log_sanity_check(self, build_log_json):
        # sanity check
        if 'log' not in build_log_json:
            build_log_json['log'] = []
        if 'warnings' not in build_log_json:
            build_log_json['warnings'] = []
        if 'errors' not in build_log_json:
            build_log_json['errors'] = []

    def unzip_converted_files(self, converted_zip_file):
        unzip_dir = tempfile.mkdtemp(prefix='unzip_', dir=self.temp_dir)
        try:
            self.logger.debug('Unzipping {0}...'.format(converted_zip_file))
            unzip(converted_zip_file, unzip_dir)
        finally:
            self.logger.debug('finished.')

        return unzip_dir

    def upload_converted_files(self, s3_commit_key, unzip_dir):
        for root, dirs, files in os.walk(unzip_dir):
            for f in sorted(files):
                path = os.path.join(root, f)
                key = s3_commit_key + path.replace(unzip_dir, '')
                self.logger.debug('Uploading {0} to {1}'.format(f, key))
                self.cdn_handler.upload_file(path, key)

    def update_project_file(self, commit_id, owner_name, repo_name):
        project_json_key = 'u/{0}/{1}/project.json'.format(owner_name, repo_name)
        project_json = self.cdn_handler.get_json(project_json_key)
        project_json['user'] = owner_name
        project_json['repo'] = repo_name
        project_json['repo_url'] = 'https://{0}/{1}/{2}'.format(self.gogs_url, owner_name, repo_name)
        commit = {
            'id': commit_id,
            'created_at': self.job.created_at,
            'status': self.job.status,
            'success': self.job.success,
            'started_at': None,
            'ended_at': None
        }
        if self.job.started_at:
            commit['started_at'] = self.job.started_at
        if self.job.ended_at:
            commit['ended_at'] = self.job.ended_at
        if 'commits' not in project_json:
            project_json['commits'] = []
        commits = []
        for c in project_json['commits']:
            if c['id'] != commit_id:
                commits.append(c)
        commits.append(commit)
        project_json['commits'] = commits
        project_file = os.path.join(self.temp_dir, 'project.json')
        write_file(project_file, project_json)
        self.cdn_handler.upload_file(project_file, project_json_key, 0)
        return project_json

    def update_build_log(self, s3_base_key, part=''):
        build_log_json = self.get_build_log(s3_base_key, part)
        self.upload_build_log(build_log_json, s3_base_key, part)
        return build_log_json

    def upload_build_log(self, build_log_json, s3_base_key, part=''):
        build_log_json['started_at'] = self.job.started_at
        build_log_json['ended_at'] = self.job.ended_at
        build_log_json['success'] = self.job.success
        build_log_json['status'] = self.job.status
        build_log_json['message'] = self.job.message
        if self.job.log:
            build_log_json['log'] = self.job.log
        else:
            build_log_json['log'] = []
        if self.job.warnings:
            build_log_json['warnings'] = self.job.warnings
        else:
            build_log_json['warnings'] = []
        if self.job.errors:
            build_log_json['errors'] = self.job.errors
        else:
            build_log_json['errors'] = []
        build_log_key = self.get_build_log_key(s3_base_key, part)
        self.logger.debug('Writing build log to ' + build_log_key)
        # self.logger.debug('build_log contents: ' + json.dumps(build_log_json))
        self.cdn_upload_contents(build_log_json, build_log_key)
        return build_log_json

    def cdn_upload_contents(self, contents, key):
        file_name = os.path.join(self.temp_dir, 'contents.json')
        write_file(file_name, contents)
        self.logger.debug('Writing file to ' + key)
        self.cdn_handler.upload_file(file_name, key, 0)

    def get_build_log(self, s3_base_key, part=''):
        build_log_key = self.get_build_log_key(s3_base_key, part)
        # self.logger.debug('Reading build log from ' + build_log_key)
        build_log_json = self.cdn_handler.get_json(build_log_key)
        # self.logger.debug('build_log contents: ' + json.dumps(build_log_json))
        return build_log_json

    def get_build_log_key(self, s3_base_key, part=''):
        upload_key = '{0}/{1}build_log.json'.format(s3_base_key, part)
        return upload_key
