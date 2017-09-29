from __future__ import print_function, unicode_literals
import os
import tempfile
from libraries.app.app import App
from libraries.general_tools import file_utils
from libraries.general_tools.file_utils import unzip, write_file, remove_tree, remove
from libraries.models.job import TxJob


class ClientLinterCallback(object):

    def __init__(self, identifier, success, info, warnings, errors, s3_results_key):
        """
        :param identifier: either
                    job_id/part_count/part_id/book if multi-part job
                        or
                    job_id if single job
        :param bool success:
        :param list info:
        :param list warnings:
        :param list errors:
        :param s3_results_key: format
                    u/user/repo/commid_id if single part
                        or
                    u/user/repo/commid_id/part_id if multi-part job
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
        self.multipart = len(id_parts) > 3
        if self.multipart:
            job_id, part_count, part_id, book = id_parts[:4]
            App.logger.debug('Multiple project, part {0} of {1}, linted book {2}'.
                             format(part_id, part_count, book))
            s3__master_results_key = '/'.join(self.s3_results_key.split('/')[:-1])
        else:
            App.logger.debug('Single project')
            s3__master_results_key = self.s3_results_key

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

        results = ClientLinterCallback.deploy_if_conversion_finished(s3__master_results_key, self.identifier)
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
    def deploy_if_conversion_finished(s3_results_key, identifier):
        """
        check if all parts are finished, and if so then save merged build_log as well as update jobs table
        :param s3_results_key: format - u/user/repo/commid_id
        :param identifier: either
                    job_id/part_count/part_id/book if multi-part job
                        or
                    job_id if single job
        :return:
        """
        output_dir = tempfile.mkdtemp(suffix="", prefix="client_callback_deploy_")
        build_log = None
        id_parts = identifier.split('/')
        multiple_project = len(id_parts) > 3

        if not multiple_project:
            App.logger.debug('Single job: checking if convert and lint have complete.')
            build_log = ClientLinterCallback.merge_build_status_for_part(build_log, s3_results_key, output_dir)
        else:
            App.logger.debug('Multiple parts: Checking if all parts completed.')
            job_id, part_count, part_id, book = id_parts[:4]
            for i in range(0, int(part_count)):
                part_key = "{0}/{1}".format(s3_results_key, i)
                build_log = ClientLinterCallback.merge_build_status_for_part(build_log, part_key, output_dir)
                if build_log is None:
                    App.logger.debug('Part {0} not complete'.format(part_key))
                    break

        if build_log is not None:  # if all parts found, save build log and kick off deploy
            # set overall status
            if len(build_log['errors']):
                build_log['status'] = 'errors'
            elif len(build_log['warnings']):
                build_log['status'] = 'warnings'

            ClientLinterCallback.upload_build_log(build_log, "build_log.json", output_dir, s3_results_key)
            ClientLinterCallback.update_project_file(build_log, output_dir)
            App.logger.debug('All parts completed, deploying')
        else:
            App.logger.debug('Not all parts completed')

        file_utils.remove_tree(output_dir)
        return build_log

    @staticmethod
    def update_jobs_table(s3_results_key, build_log, output_dir):
        job_id = build_log['job_id']
        App.logger.debug('merging build_logs for job : ' + job_id)
        job = TxJob.get(job_id)
        if job:
            job.status = build_log['status']
            job.log = build_log['log']
            job.warnings = build_log['warnings']
            job.errors = build_log['errors']
            job.message = build_log['message']
            job.success = build_log['success']

            # set overall status
            if len(job.errors):
                job.status = 'errors'
                job.success = False
            elif len(job.warnings):
                job.status = 'warnings'

            job.update()
        else:
            job_data = {}
            for key in build_log:
                if hasattr(TxJob, key):
                    job_data[key] = build_log[key]
            job = TxJob(**job_data)
            job.insert()

        ClientLinterCallback.upload_build_log(build_log, 'merged.json', output_dir, s3_results_key)
        return

    @staticmethod
    def merge_build_status_for_part(build_log, s3_results_key, output_dir):
        """
        merges convert and linter status for this part of conversion into build_log.  Returns None if part not finished.
        :param output_dir:
        :param build_log:
        :param s3_results_key:
        :return:
        """
        part_build_log = ClientLinterCallback.get_results(s3_results_key, "merged.json")  # see if already merged
        if not part_build_log:
            convert_finished = ClientLinterCallback.is_convert_finished(s3_results_key)
            if not convert_finished:
                App.logger.debug('Convert not finished for {0}'.format(s3_results_key))
                return None

            part_build_log = ClientLinterCallback.get_results(s3_results_key, "build_log.json")
            if part_build_log:
                part_build_log_combined = ClientLinterCallback.merge_build_status_for_file(part_build_log,
                                                                                           s3_results_key,
                                                                                           "lint_log.json",
                                                                                           linter_file=True)
                if part_build_log_combined:
                    if build_log:
                        ClientLinterCallback.merge_results_logs(build_log, part_build_log_combined, linter_file=False)
                    else:
                        build_log = part_build_log_combined
                    ClientLinterCallback.update_jobs_table(s3_results_key, part_build_log_combined, output_dir)
                    return build_log
                else:
                    App.logger.debug('Lint_log.json not found for {0}'.format(s3_results_key))
            else:
                App.logger.debug('Build_log.json not found for {0}'.format(s3_results_key))

            return None

        else:
            ClientLinterCallback.merge_results_logs(build_log, part_build_log, linter_file=False)
            return build_log

    @staticmethod
    def is_convert_finished(s3_results_key):
        key = "{0}/{1}".format(s3_results_key, 'finished')
        try:
            convert_finished = App.cdn_s3_handler().key_exists(key)
        except Exception as e:
            convert_finished = False
        return convert_finished

    @staticmethod
    def get_results(s3_results_key, file_name):
        key = "{0}/{1}".format(s3_results_key, file_name)
        file_results = App.cdn_s3_handler().get_json(key)
        return file_results

    @staticmethod
    def merge_build_status_for_file(build_log, s3_results_key, file_name, linter_file=False):
        key = "{0}/{1}".format(s3_results_key, file_name)
        file_results = App.cdn_s3_handler().get_json(key)
        if file_results:
            if build_log is None:
                build_log = file_results
            else:
                ClientLinterCallback.merge_results_logs(build_log, file_results, linter_file)

            return build_log
        return None

    @staticmethod
    def merge_results_logs(build_log, file_results, linter_file):
        ClientLinterCallback.merge_lists(build_log, file_results, 'log')
        ClientLinterCallback.merge_lists(build_log, file_results, 'warnings')
        ClientLinterCallback.merge_lists(build_log, file_results, 'errors')
        if not linter_file and ('success' in file_results) and (file_results['success'] is False):
            build_log['success'] = file_results['success']

    @staticmethod
    def merge_lists(build_log, file_results, key):
        if key in file_results:
            value = file_results[key]
            build_log[key] += value

    @staticmethod
    def update_project_file(build_log, output_dir):
        commit_id = build_log['commit_id']
        user_name = build_log['repo_owner']
        repo_name = build_log['repo_name']
        project_json_key = 'u/{0}/{1}/project.json'.format(user_name, repo_name)
        project_json = App.cdn_s3_handler().get_json(project_json_key)
        project_json['user'] = user_name
        project_json['repo'] = repo_name
        project_json['repo_url'] = 'https://{0}/{1}/{2}'.format(App.gogs_url, user_name, repo_name)
        commit = {
            'id': commit_id,
            'created_at': build_log['created_at'],
            'status': build_log['status'],
            'success': build_log['success'],
            'started_at': None,
            'ended_at': None
        }
        if 'started_at' in build_log:
            commit['started_at'] = build_log['started_at']
        if 'ended_at' in build_log:
            commit['ended_at'] = build_log['ended_at']
        if 'commits' not in project_json:
            project_json['commits'] = []
        commits = []
        for c in project_json['commits']:
            if c['id'] != commit_id:
                commits.append(c)
        commits.append(commit)
        project_json['commits'] = commits
        project_file = os.path.join(output_dir, 'project.json')
        write_file(project_file, project_json)
        App.cdn_s3_handler().upload_file(project_file, project_json_key, 0)
        return project_json
