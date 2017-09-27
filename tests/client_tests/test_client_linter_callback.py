from __future__ import absolute_import, unicode_literals, print_function
import json
import tempfile
import os
import shutil
from libraries.general_tools import file_utils
from mock import patch
from unittest import TestCase
from libraries.client.client_callback import ClientCallback
from moto import mock_s3
from libraries.app.app import App
from libraries.general_tools.file_utils import unzip
from libraries.linters.client_linter_callback import ClientLinterCallback


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

        try:
            os.makedirs(self.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='callbackTest_')
        self.transferred_files = []
        self.raiseDownloadException = False
        self.source_folder = None

        self.callback_data_single = {
            'identifier': 'dummy_id',
            's3_results_key': 'results',
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

    #
    # helpers
    #

    def unzip_resource_files(self, resource_file_name):
        self.source_zip = os.path.join(self.resources_dir, "conversion_callback", resource_file_name)
        self.source_folder = tempfile.mkdtemp(dir=self.temp_dir, prefix='sources_')
        unzip(self.source_zip, self.source_folder)
        source_subfolder = os.path.join(self.source_folder, resource_file_name.split('.')[0])
        results_subFolder = os.path.join(self.source_folder, 'results')
        file_utils.copy_tree(source_subfolder, results_subFolder)

    def validate_results(self, results, linter_cb):
        self.assertIsNotNone(results)
        self.assertEqual(len(results['errors']), self.expected_error_count)
        self.assertEqual(len(results['warnings']), self.expected_warning_count)
        self.assertEqual(len(results['log']), self.expected_log_count)
        self.assertEqual(results['status'], self.expected_status)
        self.assertEqual(results['success'], self.expected_success)

    def mock_client_linter_callback(self, error=None):
        clcb = ClientLinterCallback(identifier=self.callback_data_single['identifier'],
                                    success=self.callback_data_single['success'],
                                    info=self.callback_data_single['info'],
                                    warnings=self.callback_data_single['warnings'],
                                    errors=self.callback_data_single['errors'],
                                    s3_results_key=self.callback_data_single['s3_results_key'])
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
        return json_data

    def generate_parts_completed(self, start, end):
        self.parts = []
        for i in range(start, end):
            part = Part("{0}/finished".format(i))
            self.parts.append(part)
        return self.parts

    def mock_cdn_get_objects(self, prefix=None, suffix=None):
        return self.parts


class Part(object):
    def __init__(self, key):
        self.key = key
