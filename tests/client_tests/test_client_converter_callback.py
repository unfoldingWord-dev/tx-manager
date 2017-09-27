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
        App.cdn_s3_handler().get_objects = self.mock_cdn_get_objects
        App.cdn_s3_handler().upload_file = self.mock_cdn_upload_file
        App.cdn_s3_handler().get_json = self.mock_cdn_get_json
        self.init_items()
        self.populate_table()

        try:
            os.makedirs(self.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='callbackTest_')
        self.transferred_files = []
        self.raiseDownloadException = False

    def tearDown(self):
        """Runs after each test."""
        App.db_close()
        shutil.rmtree(self.base_temp_dir, ignore_errors=True)

    def init_items(self):
        self.items = {
            'job1': {
                'job_id': 'job1',
                'identifier': 'user1/repo1/commit1',
                'owner_name': 'user1',
                'repo_name': 'repo1',
                'commit_id': 'commit1',
                'user': 'user1',
                'status': 'started',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'convert_md2html',
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
                'callback': 'https://client/callback',
                'links': {'link': 'https://some/link'},
                'success': False,
                'message': 'Started',
                'log': ['Started job'],
                'warnings': ['Linter warning'],
                'errors': []
            },
            'job2': {
                'job_id': 'job2',
                'identifier': 'tx-manager-test-data/en-ulb-jud/22f3d09f7a',
                'owner_name': 'tx-manager-test-data',
                'repo_name': 'en-ulb-jud',
                'commit_id': '22f3d09f7a',
                'user': 'user1',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
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
                'message': 'Requested',
                'log': ['Requestedjob'],
                'warnings': ['Linter warning'],
                'errors': ['error']
            },
            'job3': {
                'job_id': 'job3',
                'identifier': 'user1/repo1/commit1',
                'owner_name': 'user1',
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
                'warnings': [],
                'errors': []
            },
        }

    def populate_table(self):
        for idx in self.items:
            tx_job = TxJob(**self.items[idx])
            tx_job.insert()

    @patch('libraries.client.client_callback.download_file')
    def test_clientCallbackSimpleJob(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'job2'
        mock_ccb = self.mock_client_converter_callback(identifier, mock_download_file)
        expect_error = False

        # when
        results = mock_ccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_callback.download_file')
    def test_clientCallbackMultipleJobPartial(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a/2/1/01-GEN.usfm'
        self.generate_parts_completed(1, 2)
        mock_ccb = self.mock_client_converter_callback(identifier, mock_download_file)
        expect_error = False

        # when
        results = mock_ccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_callback.download_file')
    def test_clientCallbackMultipleJobComplete(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a/2/0/01-GEN.usfm'
        self.generate_parts_completed(0, 2)
        mock_ccb = self.mock_client_converter_callback(identifier, mock_download_file)
        expect_error = False

        # when
        results = mock_ccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_callback.download_file')
    def test_clientCallbackMultipleJobCompleteError(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a/2/0/01-GEN.usfm'
        self.generate_parts_completed(0, 2)
        mock_ccb = self.mock_client_converter_callback(identifier, mock_download_file, 'conversion failed')
        expect_error = True

        # when
        results = mock_ccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_callback.download_file')
    def test_clientCallbackMultipleNoJobsComplete(self, mock_download_file):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a/2/0/01-GEN.usfm'
        self.generate_parts_completed(0, 0)
        mock_ccb = self.mock_client_converter_callback(identifier, mock_download_file)
        expect_error = False

        # when
        results = mock_ccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    @patch('libraries.client.client_callback.download_file')
    def test_clientCallbackDownloadException(self, mock_download_file):
        # given
        self.raiseDownloadException = True
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a/01-GEN.usfm'
        mock_ccb = self.mock_client_converter_callback(identifier, mock_download_file)
        expect_error = True

        # when
        results = mock_ccb.process_callback()

        # then
        self.validate_results(expect_error, results)

    #
    # helpers
    #

    def validate_results(self, expect_error, results):
        self.assertIsNotNone(results)
        error_count = len(results['errors'])
        if expect_error:
            self.assertGreater(error_count, 0)
        else:
            self.assertEquals(error_count, 0)

    def mock_client_converter_callback(self, identifier, mock_download_file, error=None):
        mock_download_file.side_effect = self.mock_download_file
        self.build_log_json = {
            'dummy_data': 'stuff',
            'commit_id':  '123456ff',
            'created_at': '2017-05-22T13:39:15Z',
            'started_at': '2017-05-22T13:39:16Z',
            'repo_owner': 'repo_owner1',
            'repo_name':  'repo_name2',
            'resource_type': 'resource_type3'
        }
        if error:
            self.build_log_json['errors'] = [error]

        self.build_log_json = json.dumps(self.build_log_json)

        self.project_json = '{}'

        job_data = {
            'job_id': '123',
            'created_at': '2017-05-22T13:39:15Z',
            'identifier': ('%s' % identifier),
            'output':     'https://test-cdn.door43.org/tx/job/6864ae1b91195f261ba5cda62d58d5ad9333f3131c787bb68f20c27adcc85cad.zip',
            'ended_at':   '2017-05-22T13:39:17Z',
            'started_at': '2017-05-22T13:39:16Z',
            'status':     'started',
            'success':    'success'
        }

        ccb = ClientConverterCallback(job_data=job_data)
        return ccb

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
        self.transferred_files.append({'type': 'upload', 'file': project_file,
                                                    'key': s3_key})
        return

    def mock_cdn_get_json(self, s3_key):
        self.transferred_files.append({'type': 'download', 'file': 'json', 'key': s3_key})
        if 'build_log.json' in s3_key:
            return json.loads(self.build_log_json)
        elif 'project.json' in s3_key:
            return json.loads(self.project_json)
        return ''

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
