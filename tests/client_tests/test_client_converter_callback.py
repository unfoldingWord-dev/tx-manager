from __future__ import absolute_import, unicode_literals, print_function
import json
import tempfile
import os
import shutil
from mock import patch
from unittest import TestCase
from moto import mock_s3
from datetime import datetime, timedelta
from libraries.app.app import App
from libraries.general_tools.file_utils import unzip
from libraries.models.job import TxJob
from libraries.general_tools import file_utils
from libraries.client.client_converter_callback import ClientConverterCallback


@mock_s3
class TestClientConverterCallback(TestCase):
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'client_converter_callback')
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
        App.cdn_s3_handler().upload_file = self.mock_cdn_upload_file
        App.cdn_s3_handler().get_json = self.mock_cdn_get_json
        App.cdn_s3_handler().key_exists = self.mock_cdn_key_exists
        self.init_items()
        self.populate_table()

        try:
            os.makedirs(self.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='callbackTest_')
        self.transferred_files = []
        self.raiseDownloadException = False
        self.s3_results_key = 'u/results'
        self.source_folder = tempfile.mkdtemp(dir=self.temp_dir, prefix='sources_')

    def tearDown(self):
        """Runs after each test."""
        App.db_close()
        shutil.rmtree(self.base_temp_dir, ignore_errors=True)

    def init_items(self):
        self.items = {
            'job1': {
                'job_id': 'job1',
                'identifier': 'tx-manager-test-data/en-ulb/22f3d09f7a',
                'user_name': 'tx-manager-test-data',
                'repo_name': 'en-ulb',
                'commit_id': '22f3d09f7a',
                'user': 'user1',
                'status': 'started',
                'resource_type': 'obs',
                'input_format': 'usfm',
                'output_format': 'html',
                'convert_module': 'convert_usfm2html',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=1),
                'started_at': None,
                'ended_at': None,
                'eta': datetime.utcnow() + timedelta(minutes=5),
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bd.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750d.zip',
                'cdn_bucket': 'cdn.door43.org',
                'cdn_file': 'u/user1/repo1',
                'callback': 'https://client/callback',
                'links': {'link': 'https://some/link'},
                'success': False,
                'message': 'Started',
                'log': ['Started job'],
                'warnings': ['warning'],
                'errors': [],
                'manifests_id': 1
            },
            'job2': {
                'job_id': 'job2',
                'identifier': 'tx-manager-test-data/en-ulb-jud/22f3d09f7a',
                'user_name': 'tx-manager-test-data',
                'repo_name': 'en-ulb-jud',
                'commit_id': '22f3d09f7a',
                'user': 'user1',
                'status': 'started',
                'resource_type': 'obs',
                'input_format': 'usfm',
                'output_format': 'html',
                'convert_module': 'convert_usfm2html',
                'cdn_bucket': 'cdn.door43.org',
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bd.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750d.zip',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=1),
                'started_at': None,
                'ended_at': None,
                'eta': datetime.utcnow() + timedelta(minutes=5),
                'cdn_file': 'u/user1/repo1',
                'callback': 'https://client/callback',
                'links': {'link': 'https://some/link'},
                'success': False,
                'message': 'Started',
                'log': ['Started job'],
                'warnings': ['warning'],
                'errors': [],
                'manifests_id': 2
            },
            'job3': {
                'job_id': 'job3',
                'identifier': 'user1/repo1/commit1',
                'user_name': 'user1',
                'repo_name': 'repo1',
                'commit_id': 'commit1',
                'user': 'user1',
                'status': 'requested',
                'resource_type': 'ulb',
                'input_format': 'usfm',
                'output_format': 'html',
                'callback': None,
                'convert_module': 'module1',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=1),
                'started_at': None,
                'ended_at': None,
                'eta': datetime.utcnow() + timedelta(minutes=5),
                'source': 'https://some/url',
                'output': 'u/user1/repo1',
                'cdn_bucket': 'cdn.door43.org',
                'cdn_file': 'u/user1/repo1',
                'links': {'link': 'https://some/link'},
                'success': False,
                'message': 'Requested',
                'log': ['Requested job'],
                'warnings': ['warning'],
                'errors': ['error'],
                'manifests_id': 3
            },
        }

    def populate_table(self):
        for idx in self.items:
            tx_job = TxJob(**self.items[idx])
            tx_job.insert()

    @patch('libraries.client.client_converter_callback.download_file')
    def test_client_client_converter_callback_simple_job(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'job2'
        mock_cccb = self.mock_client_converter_callback(identifier, mock_download_file)
        self.generate_single_job_completed()
        expect_error = False

        # when
        results = mock_cccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_converter_callback.download_file')
    def test_client_callback_multiple_job_partial(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'job1/2/1/01-GEN.usfm'
        mock_cccb = self.mock_client_converter_callback(identifier, mock_download_file)
        self.generate_parts_completed(1, 2)
        expect_error = False

        # when
        results = mock_cccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_converter_callback.download_file')
    def test_client_converter_callback_multiple_job_complete(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'job1/2/0/01-GEN.usfm'
        mock_cccb = self.mock_client_converter_callback(identifier, mock_download_file)
        self.generate_parts_completed(0, 2)
        expect_error = False

        # when
        results = mock_cccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_converter_callback.download_file')
    def test_client_converter_callback_multiple_job_complete_error(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'job1/2/0/01-GEN.usfm'
        tx_job = TxJob.get('job1')
        tx_job.errors = ['conversion failed']
        tx_job.update()
        self.s3_results_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a/0'
        mock_cccb = self.mock_client_converter_callback(identifier, mock_download_file)
        self.generate_parts_completed(0, 2)
        expect_error = True

        # when
        results = mock_cccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_converter_callback.download_file')
    def test_client_converter_callback_multiple_noo_jobs_complete(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'job1/2/0/01-GEN.usfm'
        mock_cccb = self.mock_client_converter_callback(identifier, mock_download_file)
        self.generate_parts_completed(0, 0)
        expect_error = False

        # when
        results = mock_cccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_converter_callback.download_file')
    def test_client_converter_callback_download_exception(self, mock_download_file):
        # given
        self.raiseDownloadException = True
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'job1/01-GEN.usfm'
        mock_cccb = self.mock_client_converter_callback(identifier, mock_download_file)
        expect_error = True

        # when
        results = mock_cccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    #
    # helpers
    #

    def get_results_folder(self):
        build_log_path = os.path.join(self.source_folder, self.s3_results_key)
        return build_log_path

    def get_source_path(self, file_name='build_log.json'):
        build_log_path = os.path.join(self.source_folder, self.s3_results_key,
                                      file_name)
        return build_log_path

    def unzip_resource_files(self, resource_file_name):
        self.source_zip = os.path.join(self.resources_dir, "conversion_callback", resource_file_name)
        self.source_folder = tempfile.mkdtemp(dir=self.temp_dir, prefix='sources_')
        unzip(self.source_zip, self.source_folder)
        source_subfolder = os.path.join(self.source_folder, resource_file_name.split('.')[0])
        results_subfolder = os.path.join(self.source_folder, self.results_key)
        file_utils.copy_tree(source_subfolder, results_subfolder)

    def validate_results(self, expect_error, results):
        self.assertIsNotNone(results)
        error_count = len(results['errors'])
        if expect_error:
            self.assertGreater(error_count, 0)
        else:
            self.assertEquals(error_count, 0)

    def mock_client_converter_callback(self, identifier, mock_download_file, errors=None):
        """
        :param string identifier:
        :param mock_download_file:
        :param list errors:
        :return ClientConverterCallback:
        """
        mock_download_file.side_effect = self.mock_download_file
        if not errors:
            errors = []
        self.build_log_json = {
            'dummy_data': 'stuff',
            'commit_id':  '123456ff',
            'created_at': '2017-05-22T13:39:15Z',
            'started_at': '2017-05-22T13:39:16Z',
            'repo_owner': 'repo_owner1',
            'repo_name':  'repo_name2',
            'resource_type': 'resource_type3',
            'errors': errors
        }
        self.build_log_json = json.dumps(self.build_log_json)
        self.project_json = '{}'
        cccb = ClientConverterCallback(identifier=identifier, success=True, info=[], warnings=[], errors=[])
        return cccb

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
        data = {}
        master_key = '/'.join(self.s3_results_key.split('/')[:-1])
        for i in range(start, end):
            key = "{0}/{1}/finished".format(master_key, i)
            self.save_data_to_s3(key, data)
            key = "{0}/{1}/build_log.json".format(master_key, i)
            self.save_data_to_s3(key, self.build_log_json)

    def save_data_to_s3(self, key, data):
        file_name = key.split('/')[-1:]
        output_file = tempfile.mktemp(suffix="_" + file_name[0], dir=self.temp_dir)
        file_utils.write_file(output_file, data)
        self.mock_cdn_upload_file(output_file, key)

    def generate_single_job_completed(self):
        data = {}
        key = "{0}/finished".format(self.s3_results_key)
        self.save_data_to_s3(key, data)
        key = "{0}/build_log.json".format(self.s3_results_key)
        self.save_data_to_s3(key, self.build_log_json)

    def mock_cdn_key_exists(self, key, bucket_name=None):
        source_path = os.path.join(self.source_folder, key)
        exists = os.path.exists(source_path)
        return exists
