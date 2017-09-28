from __future__ import print_function, unicode_literals
import os
import tempfile
from libraries.app.app import App
from libraries.general_tools.file_utils import write_file, remove_tree


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
        self.all_parts_completed = False
        self.multipart = False

        if not self.log:
            self.log = []
        if not self.warnings:
            self.warnings = []
        if not self.errors:
            self.errors = []
        self.temp_dir = tempfile.mkdtemp(suffix="", prefix="client_callback_")
        self.s3_results_key = s3_results_key

    def process_callback(self):
        if not self.identifier:
            error = 'No identifier found'
            App.logger.error(error)
            raise Exception(error)

        if not self.s3_results_key:
            error = 'No s3_results_key found for identifier = {0}'.format(self.identifier)
            App.logger.error(error)
            raise Exception(error)

        id_parts = self.identifier.split('/')
        self.multipart = len(id_parts) > 5
        if self.multipart:
            user, repo, commit, part_count, part_id, book = id_parts[:6]
            App.logger.debug('Multiple project, part {0} of {1}, linted book {2}'.
                             format(part_id, part_count, book))
        else:
            App.logger.debug('Single project')

        build_log = {
            'identifier': self.identifier,
            'success': self.success,
            'multipart_project': self.multipart,
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
            App.logger.debug("Linter {0} warnings:\n{1}".format(self.identifier, '\n'.join(self.warnings)))

        has_warnings = len(build_log['warnings']) > 0
        if has_warnings:
            msg = "Linter {0} has Warnings!".format(self.identifier)
            build_log['log'].append(msg)
        else:
            msg = "Linter {0} completed with no warnings".format(self.identifier)
            build_log['log'].append(msg)

        ClientLinterCallback.upload_build_log(build_log, 'lint_log.json', self.temp_dir, self.s3_results_key)

        results = ClientLinterCallback.deploy_if_conversion_finished(self.s3_results_key, self.identifier, self.temp_dir)
        if results:
            self.all_parts_completed = True
            build_log = results

        remove_tree(self.temp_dir)  # cleanup
        return build_log

    @staticmethod
    def upload_build_log(build_log, file_name, output_dir, s3_results_key):
        build_log_file = os.path.join(output_dir, file_name)
        write_file(build_log_file, build_log)
        upload_key = '{0}/{1}'.format(s3_results_key, file_name)
        App.logger.debug('Saving build log to ' + upload_key)
        App.cdn_s3_handler().upload_file(build_log_file, upload_key, cache_time=0)

    @staticmethod
    def deploy_if_conversion_finished(s3_results_key, identifier, output_dir):
        build_log = None
        master_s3_key = s3_results_key
        id_parts = identifier.split('/')
        multiple_project = len(id_parts) > 5

        if not multiple_project:
            build_log = ClientLinterCallback.merge_build_status_for_part(build_log, master_s3_key)
        else:
            user, repo, commit, part_count, part_id, book = id_parts[:6]
            master_s3_key = '/'.join(s3_results_key.split('/')[:-1])
            for i in range(0, int(part_count)):
                part_key = "{0}/{1}".format(master_s3_key, i)
                build_log = ClientLinterCallback.merge_build_status_for_part(build_log, part_key)
                if build_log is None:
                    break

        if build_log is not None:  # if all parts found, save build log and kick off deploy
            # set overall status
            if len(build_log['errors']):
                build_log['status'] = 'errors'
            elif len(build_log['warnings']):
                build_log['status'] = 'warnings'
            ClientLinterCallback.upload_build_log(build_log, "build_log.json", output_dir, master_s3_key)

        return build_log

    @staticmethod
    def merge_build_status_for_part(build_log, s3_results_key):
        """
        merges convert and linter status for this part of conversion into build_log.  Returns None if part not finished.
        :param build_log:
        :param s3_results_key:
        :return:
        """
        results = ClientLinterCallback.merge_build_status_for_file(build_log, s3_results_key, "build_log.json")
        if results:
            build_log = results
            results = ClientLinterCallback.merge_build_status_for_file(build_log, s3_results_key, "lint_log.json",
                                                                       linter_file=True)
            if results:
                return results

        return None

    @staticmethod
    def merge_build_status_for_file(build_log, s3_results_key, file_name, linter_file=False):
        key = "{0}/{1}".format(s3_results_key, file_name)
        file_results = App.cdn_s3_handler().get_json(key)
        if file_results:
            if build_log is None:
                build_log = file_results
            else:
                ClientLinterCallback.merge_lists(build_log, file_results, 'log')
                ClientLinterCallback.merge_lists(build_log, file_results, 'warnings')
                ClientLinterCallback.merge_lists(build_log, file_results, 'errors')
                if not linter_file and ('success' in file_results) and (file_results['success'] is False):
                    build_log['success'] = file_results['success']

            return build_log
        return None

    @staticmethod
    def merge_lists(build_log, file_results, key):
        if key in file_results:
            value = file_results[key]
            build_log[key] += value
