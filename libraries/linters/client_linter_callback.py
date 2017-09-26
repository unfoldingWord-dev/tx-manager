from __future__ import print_function, unicode_literals
import json
import os
import tempfile
from libraries.app.app import App
from libraries.general_tools.file_utils import unzip, write_file, remove_tree, remove
from libraries.general_tools.url_utils import download_file
from libraries.models.job import TxJob


class ClientLinterCallback(object):

    def __init__(self, identifier, success, info, warnings, errors, s3_results_key):
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

        if not self.log:
            self.log = []
        if not self.warnings:
            self.warnings = []
        if not self.errors:
            self.errors = []
        self.temp_dir = tempfile.mkdtemp(suffix="", prefix="client_callback_")
        self.s3_results_key = s3_results_key

    def process_converter_callback(self):

        if not self.identifier:
            error = 'No identifier found'
            App.logger.error(error)
            raise Exception(error)

        if not self.s3_results_key:
            error = 'No s3_commit_key found for identifier = {0}'.format(self.identifier)
            App.logger.error(error)
            raise Exception(error)

        job_id_parts = self.identifier.split('/')
        job_id = job_id_parts[0]

        multiple_project = len(job_id_parts) == 4
        if multiple_project:
            part_count, part_id, book = job_id_parts[1:]
            App.logger.debug('Multiple project, part {0} of {1}, linted book {2}'.
                             format(part_id, part_count, book))
        else:
            App.logger.debug('Single project')

        build_log = {
            'job_id': job_id,
            'identifier': self.identifier,
            'success': self.success,
            'multiple_project': multiple_project,
            'log': self.log,
            'warnings': self.warnings,
            'errors': self.errors,
            's3_commit_key': self.s3_results_key
        }

        if not self.success:
            msg = "Linter failed for identifier: " + self.identifier
            build_log['warnings'].append(msg)
            App.logger.error(msg)
        else:
            App.logger.debug("Linter {0} results:\n{1}".format(self.identifier, '\n'.join(self.warnings)))

        has_warnings = len(build_log['warnings']) > 0
        if has_warnings:
            msg = "Linter {0} has Warnings!".format(self.identifier)
            build_log['log'].append(msg)
        else:
            msg = "Linter {0} completed with no warnings".format(self.identifier)
            build_log['log'].append(msg)

        ClientLinterCallback.upload_build_log(build_log, 'linter_log.json', self.temp_dir, self.s3_results_key)

        ClientLinterCallback.check_if_conversion_finished(multiple_project, self.s3_results_key)

        remove_tree(self.temp_dir)  # cleanup
        return

    @staticmethod
    def upload_build_log(build_log, file_name, output_dir, s3_commit_key):
        build_log_file = os.path.join(output_dir, file_name)
        write_file(build_log_file, build_log)
        upload_key = '{0}/{1}'.format(s3_commit_key, file_name)
        App.logger.debug('Saving build log to ' + upload_key)
        App.cdn_s3_handler().upload_file(build_log_file, upload_key, cache_time=0)

    @staticmethod
    def check_if_conversion_finished(is_multiple_project, s3_commit_key):
        # TODO blm
        return True

    @staticmethod
    def get_build_status_for_part(s3_commit_key):
        get_file_contents()
        return True
