from __future__ import print_function, unicode_literals
import os
import tempfile
import logging
import time
from logging import Logger
from general_tools.file_utils import unzip, write_file
from general_tools.url_utils import download_file
from aws_tools.s3_handler import S3Handler
from manager.job import TxJob


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

    def process_callback(self):
        cdn_handler = S3Handler(self.cdn_bucket)
        owner_name, repo_name, commit_id = self.job.identifier.split('/')
        # The identifier is how to know which username/repo/commit this callback goes to
        s3_commit_key = 'u/{0}/{1}/{2}'.format(owner_name, repo_name, commit_id)

        # Download the ZIP file of the converted files
        converted_zip_url = self.job.output
        converted_zip_file = os.path.join(tempfile.gettempdir(), converted_zip_url.rpartition('/')[2])
        try:
            self.logger.debug('Downloading converted zip file from {0}...'.format(converted_zip_url))
            tries = 0
            # Going to try to get the file every second for 200 seconds just in case there is a delay in the upload
            # (For example, 3.6MB takes at least one minute to be seen on S3!)
            time.sleep(5)
            while not os.path.isfile(converted_zip_file) and tries < 200:
                tries += 1
                time.sleep(1)
                try:
                    download_file(converted_zip_url, converted_zip_file)
                except:
                    if tries >= 200:
                        raise
        finally:
            self.logger.debug('finished.')

        # Unzip the archive
        unzip_dir = tempfile.mkdtemp(prefix='unzip_')
        try:
            self.logger.debug('Unzipping {0}...'.format(converted_zip_file))
            unzip(converted_zip_file, unzip_dir)
        finally:
            self.logger.debug('finished.')

        # Upload all files to the cdn_bucket with the key of <user>/<repo_name>/<commit> of the repo
        for root, dirs, files in os.walk(unzip_dir):
            for f in sorted(files):
                path = os.path.join(root, f)
                key = s3_commit_key + path.replace(unzip_dir, '')
                self.logger.debug('Uploading {0} to {1}'.format(f, key))
                cdn_handler.upload_file(path, key)

        # Download the project.json file for this repo (create it if doesn't exist) and update it
        project_json_key = 'u/{0}/{1}/project.json'.format(owner_name, repo_name)
        project_json = cdn_handler.get_json(project_json_key)
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
        project_file = os.path.join(tempfile.gettempdir(), 'project.json')
        write_file(project_file, project_json)
        cdn_handler.upload_file(project_file, project_json_key, 0)

        # Now download the existing build_log.json file, update it and upload it back to S3
        build_log_json = cdn_handler.get_json(s3_commit_key + '/build_log.json')
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
        build_log_file = os.path.join(tempfile.gettempdir(), 'build_log_finished.json')
        write_file(build_log_file, build_log_json)
        cdn_handler.upload_file(build_log_file, s3_commit_key + '/build_log.json', 0)

        self.logger.debug('Finished deploying to cdn_bucket. Done.')

        return build_log_json
