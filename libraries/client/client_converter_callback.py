from __future__ import print_function, unicode_literals
import json
import os
import tempfile
from datetime import datetime
from libraries.app.app import App
from libraries.client.client_linter_callback import ClientLinterCallback
from libraries.general_tools.file_utils import unzip, write_file, remove_tree, remove
from libraries.general_tools.url_utils import download_file
from libraries.models.job import TxJob


class ClientConverterCallback(object):

    def __init__(self, identifier, success, info, warnings, errors):
        """
        :param string identifier:
        :param bool success:
        :param list info:
        :param list warnings:
        :param list errors:
        """
        self.identifier = identifier
        self.success = success
        self.log = info
        self.warnings = warnings
        self.errors = errors
        self.all_parts_completed = False

        if not self.log:
            self.log = []
        if not self.warnings:
            self.warnings = []
        if not self.errors:
            self.errors = []
        self.temp_dir = tempfile.mkdtemp(suffix="", prefix="client_callback_")
        self.job = None

    def process_callback(self):
        job_id_parts = self.identifier.split('/')
        job_id = job_id_parts[0]
        self.job = TxJob.get(job_id)

        if not self.job:
            error = 'No job found for job_id = {0}, identifier = {1}'.format(job_id, self.identifier)
            App.logger.error(error)
            raise Exception(error)

        if len(job_id_parts) == 4:
            part_count, part_id, book = job_id_parts[1:]
            App.logger.debug('Multiple project, part {0} of {1}, converting book {2}'.
                             format(part_id, part_count, book))
            multiple_project = True
        else:
            App.logger.debug('Single project')
            part_id = None
            multiple_project = False

        self.job.ended_at = datetime.utcnow()
        self.job.success = self.success
        for message in self.log:
            self.job.log_message(message)
        for message in self.warnings:
            self.job.warnings_message(message)
        for message in self.errors:
            self.job.error_message(message)
        if len(self.errors):
            self.job.log_message('{0} function returned with errors.'.format(self.job.convert_module))
        elif len(self.warnings):
            self.job.log_message('{0} function returned with warnings.'.format(self.job.convert_module))
        else:
            self.job.log_message('{0} function returned successfully.'.format(self.job.convert_module))

        if not self.success or len(self.job.errors):
            self.job.success = False
            self.job.status = "failed"
            message = "Conversion failed"
            App.logger.debug("Conversion failed, success: {0}, errors: {1}".format(self.success, self.job.errors))
        elif len(self.job.warnings) > 0:
            self.job.success = True
            self.job.status = "warnings"
            message = "Conversion successful with warnings"
        else:
            self.job.success = True
            self.job.status = "success"
            message = "Conversion successful"

        self.job.message = message
        self.job.log_message(message)
        self.job.log_message('Finished job {0} at {1}'.format(self.job.job_id, self.job.ended_at.strftime("%Y-%m-%dT%H:%M:%SZ")))

        s3_commit_key = 'u/{0}/{1}/{2}'.format(self.job.user_name, self.job.repo_name, self.job.commit_id)
        upload_key = s3_commit_key
        if multiple_project:
            upload_key += "/" + part_id

        App.logger.debug('Callback for commit {0}...'.format(s3_commit_key))

        # Download the ZIP file of the converted files
        converted_zip_url = self.job.output
        converted_zip_file = os.path.join(self.temp_dir, converted_zip_url.rpartition('/')[2])
        remove(converted_zip_file)  # make sure old file not present
        download_success = True
        App.logger.debug('Downloading converted zip file from {0}...'.format(converted_zip_url))
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
            App.logger.debug('download finished, success={0}'.format(str(download_success)))

        self.job.update()

        if download_success:
            # Unzip the archive
            unzip_dir = self.unzip_converted_files(converted_zip_file)

            # Upload all files to the cdn_bucket with the key of <user>/<repo_name>/<commit> of the repo
            self.upload_converted_files(upload_key, unzip_dir)

        if multiple_project:
            # Now download the existing build_log.json file, update it and upload it back to S3 as convert_log
            build_log_json = self.update_convert_log(s3_commit_key, part_id + "/")

            # mark current part as finished
            self.cdn_upload_contents({}, s3_commit_key + '/' + part_id + '/finished')

        else:  # single part conversion
            # Now download the existing build_log.json file, update it and upload it back to S3 as convert_log
            build_log_json = self.update_convert_log(s3_commit_key)

            self.cdn_upload_contents({}, s3_commit_key + '/finished')  # flag finished

        results = ClientLinterCallback.deploy_if_conversion_finished(s3_commit_key, self.identifier)
        if results:
            self.all_parts_completed = True
            build_log_json = results

        remove_tree(self.temp_dir)  # cleanup
        return build_log_json

    def unzip_converted_files(self, converted_zip_file):
        unzip_dir = tempfile.mkdtemp(prefix='unzip_', dir=self.temp_dir)
        try:
            App.logger.debug('Unzipping {0}...'.format(converted_zip_file))
            unzip(converted_zip_file, unzip_dir)
        finally:
            App.logger.debug('finished.')

        return unzip_dir

    @staticmethod
    def upload_converted_files(s3_commit_key, unzip_dir):
        for root, dirs, files in os.walk(unzip_dir):
            for f in sorted(files):
                path = os.path.join(root, f)
                key = s3_commit_key + path.replace(unzip_dir, '')
                App.logger.debug('Uploading {0} to {1}'.format(f, key))
                App.cdn_s3_handler().upload_file(path, key, cache_time=0)

    def update_convert_log(self, s3_base_key, part=''):
        build_log_json = self.get_build_log(s3_base_key, part)
        self.upload_convert_log(build_log_json, s3_base_key, part)
        return build_log_json

    def upload_convert_log(self, build_log_json, s3_base_key, part=''):
        if self.job.started_at:
            build_log_json['started_at'] = self.job.started_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            build_log_json['started_at'] = None
        if self.job.ended_at:
            build_log_json['ended_at'] = self.job.ended_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            build_log_json['ended_at'] = None
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
        build_log_key = self.get_build_log_key(s3_base_key, part, name='convert_log.json')
        App.logger.debug('Writing build log to ' + build_log_key)
        # App.logger.debug('build_log contents: ' + json.dumps(build_log_json))
        self.cdn_upload_contents(build_log_json, build_log_key)
        return build_log_json

    def cdn_upload_contents(self, contents, key):
        file_name = os.path.join(self.temp_dir, 'contents.json')
        write_file(file_name, contents)
        App.logger.debug('Writing file to ' + key)
        App.cdn_s3_handler().upload_file(file_name, key, cache_time=0)

    def get_build_log(self, s3_base_key, part=''):
        build_log_key = self.get_build_log_key(s3_base_key, part)
        # App.logger.debug('Reading build log from ' + build_log_key)
        build_log_json = App.cdn_s3_handler().get_json(build_log_key)
        # App.logger.debug('build_log contents: ' + json.dumps(build_log_json))
        return build_log_json

    @staticmethod
    def get_build_log_key(s3_base_key, part='', name='build_log.json'):
        upload_key = '{0}/{1}{2}'.format(s3_base_key, part, name)
        return upload_key
