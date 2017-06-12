from __future__ import print_function, unicode_literals
import os
import tempfile
import logging
import time
from logging import Logger
from general_tools import file_utils
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
        parts = self.job.identifier.split('/')
        multipleProject = len(parts) >= 5
        if not multipleProject:
            owner_name, repo_name, commit_id = parts
        else:
            owner_name, repo_name, commit_id, part_count, part_id = parts
            self.logger.debug('Multiple project, part {0} of {1}'.format(part_id,part_count))

        # The identifier is how to know which username/repo/commit this callback goes to
        s3_commit_key = 'u/{0}/{1}/{2}'.format(owner_name, repo_name, commit_id)

        self.logger.debug('Callback for comming {0}...'.format(s3_commit_key))

        # Download the ZIP file of the converted files
        converted_zip_url = self.job.output
        converted_zip_file = os.path.join(tempfile.gettempdir(), converted_zip_url.rpartition('/')[2])
        file_utils.remove(converted_zip_file) # make sure old file not present
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
                    self.downloadFile(converted_zip_file, converted_zip_url)
                except:
                    if tries >= 200:
                        raise
        finally:
            self.logger.debug('download finished.')

        if multipleProject:
            # copy this part of converted output to repo
            s3_part_key = '{0}/{1}'.format(s3_commit_key, part_id)
            self.cdnUploadFile(cdn_handler, converted_zip_file, s3_part_key + '.zip')

            self.logger.debug('download finished.')

            # check if all parts are present, if not return
            missing_parts = []
            finishedParts = self.getFinishedParts(cdn_handler, s3_commit_key)

            count = int(part_count)
            for i in range(0, count):
                fileName = '{0}.zip'.format(i)

                matchFound = False
                for part in finishedParts:
                    if fileName in part.key:
                        matchFound = True
                        break

                if not matchFound:
                    missing_parts.append(fileName)

            # Now download the existing build_log.json file, update it and upload it back to S3
            build_log_json = self.updateBuildLog(cdn_handler, s3_part_key)

            if len(missing_parts) > 0:
                self.logger.debug('Finished processing part. Other parts not yet completed: ' + ','.join(missing_parts))
                return build_log_json

            self.logger.debug('All parts finished. Merging.')

            # all parts are present, merge together

            build_logs_json = []
            self.job.status = 'success'
            self.job.log = []
            self.job.warnings = []
            self.job.errors = []
            baseTempFolder = tempfile.gettempdir()
            for i in range(0, count):
                s3_part_key = '{0}/{1}'.format(s3_commit_key, i)
                converted_zip_file = os.path.join(baseTempFolder, str(i) + '.zip')
                self.cdnDownloadFile(cdn_handler, s3_part_key + '.zip', converted_zip_file)

                # Unzip the archive
                unzip_dir = self.unzipConvertedFiles(converted_zip_file)

                # Upload all files to the cdn_bucket with the key of <user>/<repo_name>/<commit> of the repo
                self.uploadConvertedFiles(cdn_handler, s3_commit_key, unzip_dir)

                # Now download the existing build_log.json file
                build_log_file, build_log_json = self.getBuildLog(cdn_handler, s3_part_key + '/build_log.json')
                build_logs_json.append(build_log_json)

                self.job.log += build_log_json['log']
                self.job.errors += build_log_json['errors']
                self.job.warnings += build_log_json['warnings']
                if build_log_json['status'] != 'success':
                    self.job.success = build_log_json['success']
                if build_log_json['status'] != 'success':
                    self.job.status = build_log_json['status']

            # Now download the existing build_log.json file, update it and upload it back to S3
            build_log_json = self.updateBuildLog(cdn_handler, s3_commit_key)

            self.logger.debug('Multiple parts: Finished deploying to cdn_bucket. Done.')

            # Download the project.json file for this repo (create it if doesn't exist) and update it
            self.updateProjectFile(cdn_handler, commit_id, owner_name, repo_name)

            return build_log_json

        else: # single part conversion
            # Unzip the archive
            unzip_dir = self.unzipConvertedFiles(converted_zip_file)

            # Upload all files to the cdn_bucket with the key of <user>/<repo_name>/<commit> of the repo
            self.uploadConvertedFiles(cdn_handler, s3_commit_key, unzip_dir)

            # Download the project.json file for this repo (create it if doesn't exist) and update it
            self.updateProjectFile(cdn_handler, commit_id, owner_name, repo_name)

            # Now download the existing build_log.json file, update it and upload it back to S3
            build_log_json = self.updateBuildLog(cdn_handler, s3_commit_key)

            self.logger.debug('Finished deploying to cdn_bucket. Done.')
            return build_log_json

    def cdnDownloadFile(self, cdn_handler, s3_part_key, filePath):
        cdn_handler.download_file(s3_part_key + '.zip', filePath)

    def downloadFile(self, converted_zip_file, converted_zip_url):
        download_file(converted_zip_url, converted_zip_file)

    def getFinishedParts(self, cdn_handler, s3_commit_key):
        return cdn_handler.get_objects(prefix=s3_commit_key, suffix='.zip')

    def unzipConvertedFiles(self, converted_zip_file):
        unzip_dir = tempfile.mkdtemp(prefix='unzip_')
        try:
            self.logger.debug('Unzipping {0}...'.format(converted_zip_file))
            unzip(converted_zip_file, unzip_dir)
        finally:
            self.logger.debug('finished.')

        return unzip_dir

    def uploadConvertedFiles(self, cdn_handler, s3_commit_key, unzip_dir):
        for root, dirs, files in os.walk(unzip_dir):
            for f in sorted(files):
                path = os.path.join(root, f)
                key = s3_commit_key + path.replace(unzip_dir, '')
                self.logger.debug('Uploading {0} to {1}'.format(f, key))
                self.cdnUploadFile(cdn_handler, path, key)

    def cdnUploadFile(self, cdn_handler, path, key, cache_time=600):
        cdn_handler.upload_file(path, key, cache_time)

    def updateProjectFile(self, cdn_handler, commit_id, owner_name, repo_name):
        project_json_key = 'u/{0}/{1}/project.json'.format(owner_name, repo_name)
        project_json = self.cdnGetJsonFile(cdn_handler, project_json_key)
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
        self.cdnUploadFile(cdn_handler, project_file, project_json_key, 0)

    def cdnGetJsonFile(self, cdn_handler, project_json_key):
        project_json = cdn_handler.get_json(project_json_key)
        return project_json

    def updateBuildLog(self, cdn_handler, s3_commit_key):
        build_log_file, build_log_json = self.getBuildLog(cdn_handler, s3_commit_key)
        write_file(build_log_file, build_log_json)
        self.cdnUploadFile(cdn_handler, build_log_file, s3_commit_key + '/build_log.json', 0)
        return build_log_json

    def getBuildLog(self, cdn_handler, s3_commit_key):
        build_log_json = self.cdnGetJsonFile(cdn_handler, s3_commit_key + '/build_log.json')
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
        return build_log_file, build_log_json
