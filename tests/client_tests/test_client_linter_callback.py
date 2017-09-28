from __future__ import absolute_import, unicode_literals, print_function

import os
import shutil
import tempfile
from unittest import TestCase
from moto import mock_s3
from libraries.app.app import App
from libraries.client.client_linter_callback import ClientLinterCallback
from libraries.general_tools import file_utils
from libraries.general_tools.file_utils import unzip


@mock_s3
class TestClientLinterCallback(TestCase):
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'test-client-linter')
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    source_zip = ''
    build_log_json = ''
    project_json = ''
    transferred_files = []  # for keeping track of file transfers to cdn
    raiseDownloadException = False

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        App.cdn_s3_handler().create_bucket()
        App.cdn_s3_handler().get_objects = self.mock_cdn_get_objects
        App.cdn_s3_handler().upload_file = self.mock_cdn_upload_file
        App.cdn_s3_handler().get_json = self.mock_cdn_get_json
        App.cdn_s3_handler().key_exists = self.mock_cdn_key_exists

        try:
            os.makedirs(self.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='callbackTest_')
        self.transferred_files = []
        self.raiseDownloadException = False
        self.source_folder = None

        self.results_key = 'u/results'
        self.lint_callback_data = {
            'identifier': 'dummy_id',
            's3_results_key': self.results_key,
            'success': True,
            'info': [],
            'warnings': [],
            'errors': []
        }
        self.expected_error_count = 0
        self.expected_warning_count = 0
        self.expected_log_count = 0
        self.expected_status = "success"
        self.expected_success = True
        self.expected_all_parts_completed = True
        self.expected_multipart = False

    def tearDown(self):
        """Runs after each test."""
        App.db_close()
        shutil.rmtree(self.base_temp_dir, ignore_errors=True)

    def test_callbackSimpleJob(self):
        # given
        self.unzip_resource_files("id_mat_ulb.zip")
        self.expected_log_count = 9
        linter_cb = self.mock_client_linter_callback()

        # when
        results = linter_cb.process_callback()

        # then
        self.validate_results(results, linter_cb)

    def test_callbackSimpleJob_missing_id(self):
        # given
        self.expected_log_count = 9
        del self.lint_callback_data['identifier']
        exception_thrown = False

        # when
        try:
            linter_cb = self.mock_client_linter_callback()
            results = linter_cb.process_callback()
        except Exception as e:
            exception_thrown = True

        # then
        self.assertTrue(exception_thrown)

    def test_callbackSimpleJob_empty_id(self):
        # given
        self.expected_log_count = 9
        self.lint_callback_data['identifier'] = ''
        linter_cb = self.mock_client_linter_callback()
        exception_thrown = False

        # when
        try:
            results = linter_cb.process_callback()
        except Exception as e:
            exception_thrown = True

        # then
        self.assertTrue(exception_thrown)

    def test_callbackSimpleJob_empty_s3_results_key(self):
        # given
        self.expected_log_count = 9
        self.lint_callback_data['s3_results_key'] = ''
        linter_cb = self.mock_client_linter_callback()
        exception_thrown = False

        # when
        try:
            results = linter_cb.process_callback()
        except Exception as e:
            exception_thrown = True

        # then
        self.assertTrue(exception_thrown)

    def test_callbackSimpleJob_lint_error(self):  # lint error treated as build warning
        # given
        self.unzip_resource_files("id_mat_ulb.zip")
        self.lint_callback_data['success'] = False
        self.expected_log_count = 9
        self.expected_warning_count = 1
        self.expected_status = "warnings"
        linter_cb = self.mock_client_linter_callback()

        # when
        results = linter_cb.process_callback()

        # then
        self.validate_results(results, linter_cb)

    def test_callbackSimpleJob_lint_warning(self):
        # given
        self.unzip_resource_files("id_mat_ulb.zip")
        self.lint_callback_data['warnings'].append("lint warning")
        self.expected_log_count = 9
        self.expected_warning_count = 1
        self.expected_status = "warnings"
        linter_cb = self.mock_client_linter_callback()

        # when
        results = linter_cb.process_callback()

        # then
        self.validate_results(results, linter_cb)

    def test_callbackSimpleJob_build_log_missing(self):
        # given
        self.unzip_resource_files("id_mat_ulb.zip")
        build_log_path = self.get_source_path()
        file_utils.remove(build_log_path)
        self.expected_log_count = 1
        self.expected_status = None
        self.expected_all_parts_completed = False
        linter_cb = self.mock_client_linter_callback()

        # when
        results = linter_cb.process_callback()

        # then
        self.validate_results(results, linter_cb)

    def test_callbackSimpleJob_build_not_finished(self):
        # given
        self.unzip_resource_files("id_mat_ulb.zip")
        finished_path = self.get_source_path('finished')
        file_utils.remove(finished_path)
        self.expected_log_count = 1
        self.expected_status = None
        self.expected_all_parts_completed = False
        linter_cb = self.mock_client_linter_callback()

        # when
        results = linter_cb.process_callback()

        # then
        self.validate_results(results, linter_cb)

    def test_callbackSimpleJob_build_error(self):
        # given
        self.unzip_resource_files("id_mat_ulb.zip")
        build_log_path = self.get_source_path()
        build_log = file_utils.load_json_object(build_log_path)
        build_log['errors'].append('convert error')
        build_log['success'] = False
        build_log['status'] = 'errors'
        file_utils.write_file(build_log_path, build_log)
        self.expected_log_count = 9
        self.expected_error_count = 1
        self.expected_success = False
        self.expected_status = "errors"
        linter_cb = self.mock_client_linter_callback()

        # when
        results = linter_cb.process_callback()

        # then
        self.validate_results(results, linter_cb)

    def test_callbackSimpleJob_LintNotFinished(self):
        # given
        self.unzip_resource_files("id_mat_ulb.zip")
        identifier = self.lint_callback_data['identifier']

        # when
        results = ClientLinterCallback.deploy_if_conversion_finished(self.results_key, identifier)

        # then
        self.assertIsNone(results)

    def test_callbackMultpleJob(self):
        # given
        self.results_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.unzip_resource_files("en_ulb.zip")
        self.lint_callback_data['s3_results_key'] = self.results_key + '/0'
        self.lint_callback_data['identifier'] = '1234567890/4/0/01-GEN.usfm'
        self.expected_log_count = 36
        self.expected_multipart = True
        linter_cb = self.mock_client_linter_callback()

        # when
        results = linter_cb.process_callback()

        # then
        self.validate_results(results, linter_cb)

    def test_callbackMultpleJob_build_error(self):
        # given
        self.results_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.lint_callback_data['s3_results_key'] = self.results_key + '/2'
        self.lint_callback_data['identifier'] = '1234567890/4/2/03-LEV.usfm'
        self.unzip_resource_files("en_ulb.zip")
        build_log_path = self.get_source_path()
        build_log = file_utils.load_json_object(build_log_path)
        build_log['errors'].append('convert error')
        build_log['success'] = False
        build_log['status'] = 'errors'
        file_utils.write_file(build_log_path, build_log)
        self.expected_error_count = 1
        self.expected_success = False
        self.expected_status = "errors"
        self.expected_log_count = 36
        self.expected_multipart = None
        linter_cb = self.mock_client_linter_callback()

        # when
        results = linter_cb.process_callback()

        # then
        self.validate_results(results, linter_cb)

    def test_callbackMultpleJob_LintNotFinished(self):
        # given
        self.results_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.lint_callback_data['s3_results_key'] = self.results_key + '/3'
        self.lint_callback_data['identifier'] = '1234567890/4/3/05-DEU.usfm'
        self.unzip_resource_files("en_ulb.zip")
        lint_log_path = self.get_source_path()
        file_utils.remove(lint_log_path)
        identifier = self.lint_callback_data['identifier']

        # when
        results = ClientLinterCallback.deploy_if_conversion_finished(self.results_key, identifier)

        # then
        self.assertIsNone(results)


    #
    # helpers
    #

    def get_results_folder(self):
        build_log_path = os.path.join(self.source_folder, self.lint_callback_data['s3_results_key'])
        return build_log_path

    def get_source_path(self, file_name='build_log.json'):
        build_log_path = os.path.join(self.source_folder, self.lint_callback_data['s3_results_key'],
                                      file_name)
        return build_log_path

    def unzip_resource_files(self, resource_file_name):
        self.source_zip = os.path.join(self.resources_dir, "conversion_callback", resource_file_name)
        self.source_folder = tempfile.mkdtemp(dir=self.temp_dir, prefix='sources_')
        unzip(self.source_zip, self.source_folder)
        source_subfolder = os.path.join(self.source_folder, resource_file_name.split('.')[0])
        results_subFolder = os.path.join(self.source_folder, self.results_key)
        file_utils.copy_tree(source_subfolder, results_subFolder)

    def validate_results(self, results, linter_cb):
        self.assertIsNotNone(results)
        self.assertEqual(len(results['errors']), self.expected_error_count)
        self.assertEqual(len(results['warnings']), self.expected_warning_count)
        self.assertEqual(len(results['log']), self.expected_log_count)
        if self.expected_status is not None:
            self.assertEqual(results['status'], self.expected_status)
        else:
            self.assertFalse('status' in results)

        self.assertEqual(results['success'], self.expected_success)
        self.assertEqual(linter_cb.all_parts_completed, self.expected_all_parts_completed)

        if self.expected_multipart is not None:
            self.assertEqual(linter_cb.multipart, self.expected_multipart)

    def mock_client_linter_callback(self, error=None):
        clcb = ClientLinterCallback(identifier=self.lint_callback_data['identifier'],
                                    success=self.lint_callback_data['success'],
                                    info=self.lint_callback_data['info'],
                                    warnings=self.lint_callback_data['warnings'],
                                    errors=self.lint_callback_data['errors'],
                                    s3_results_key=self.lint_callback_data['s3_results_key'])
        return clcb

    def mock_download_file(self, url, target):
        if self.raiseDownloadException:
            raise Exception

        file_name = os.path.basename(url)
        if '.zip' in file_name:
            shutil.copyfile(self.source_zip, target)
        elif file_name == 'build_log.json':
            file_utils.write_file(target, self.build_log_json)
        elif file_name == 'project.json':
            file_utils.write_file(target, self.project_json)

    def mock_cdn_upload_file(self, project_file, s3_key, cache_time=600):
        destination_path = os.path.join(self.source_folder, s3_key)
        destination_folder = os.path.dirname(destination_path)
        file_utils.make_dir(destination_folder)
        shutil.copy(project_file, destination_path)
        return

    def mock_cdn_get_json(self, s3_key):
        source_path = os.path.join(self.source_folder, s3_key)
        json_data = file_utils.load_json_object(source_path)
        if not json_data:
            json_data = {}
        return json_data

    def generate_parts_completed(self, start, end):
        self.parts = []
        for i in range(start, end):
            part = Part("{0}/finished".format(i))
            self.parts.append(part)
        return self.parts

    def mock_cdn_get_objects(self, prefix=None, suffix=None):
        return self.parts

    def mock_cdn_key_exists(self, key, bucket_name=None):
        source_path = os.path.join(self.source_folder, key)
        exists = os.path.exists(source_path)
        return exists


class Part(object):
    def __init__(self, key):
        self.key = key
