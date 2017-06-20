from __future__ import absolute_import, unicode_literals, print_function
import json
import os
import shutil
import tempfile
import unittest
from aws_tools.s3_handler import S3Handler
from mock import patch
from client.client_webhook import ClientWebhook
from general_tools.file_utils import read_file
from moto import mock_s3


@mock_s3
class TestClientWebhook(unittest.TestCase):
    parent_resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    temp_dir = None
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'test-tx-manager')
    shutil.rmtree(base_temp_dir, ignore_errors=True)
    jobRequestCount = 0
    default_mock_job_return_value = {'job_id': '0', 'status': 'started', 'success': 'success', 'resource_type': 'obs',
                                     'input_format': 'md', 'output_format': 'html', 'convert_module': 'module1',
                                     'created_at': '2017-05-22T13:39:15Z', 'errors': []}
    mock_job_return_value = default_mock_job_return_value
    uploaded_files = []

    def setUp(self):
        try:
            os.makedirs(TestClientWebhook.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=TestClientWebhook.base_temp_dir, prefix='webhookTest_')
        TestClientWebhook.jobRequestCount = 0
        TestClientWebhook.mock_job_return_value = \
            json.loads(json.dumps(TestClientWebhook.default_mock_job_return_value))  # do deep copy
        TestClientWebhook.uploaded_files = []

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('client.client_webhook.download_file')
    def test_downloadRepo(self, mock_download_file):
        mock_download_file.side_effect = self.mock_download_repo
        cwh = ClientWebhook()
        try:
            os.makedirs(cwh.base_temp_dir)
        except:
            pass
        cwh.download_repo('bible_bundle_master', TestClientWebhook.base_temp_dir)

    @patch('client.client_webhook.download_file')
    def test_processWebhook(self, mock_download_file):
        # given
        client_web_hook = self.setupClientWebhookMock('kpb_mat_text_udb_repo', self.parent_resources_dir,
                                                      mock_download_file)
        expected_job_count = 1
        expected_error_count = 0

        # when
        results = client_web_hook.process_webhook()

        # then
        self.assertEqual(TestClientWebhook.jobRequestCount, expected_job_count)
        self.assertTrue(len(results['job_id']) > 16)
        self.assertFalse('multiple' in results)
        self.assertEqual(len(results['errors']), expected_error_count)
        self.assertEqual(results, self.getBuildLogJson())
        self.assertTrue(len(self.getProjectJson()) >= 4)

    @patch('client.client_webhook.download_file')
    def test_processWebhookError(self, mock_download_file):
        # given
        client_web_hook = self.setupClientWebhookMock('kpb_mat_text_udb_repo', self.parent_resources_dir,
                                                      mock_download_file)
        TestClientWebhook.mock_job_return_value['errors'] = ['error 1', 'error 2']
        expected_job_count = 1
        captured_error = False
        expected_error_count = 2

        # when
        try:
            client_web_hook.process_webhook()
        except:
            captured_error = True

        # then
        self.assertEqual(TestClientWebhook.jobRequestCount, expected_job_count)
        self.assertTrue(captured_error)
        results = self.getBuildLogJson()
        self.assertTrue(len(results['job_id']) > 16)
        self.assertFalse('multiple' in results)
        self.assertEqual(len(results['errors']), expected_error_count)
        self.assertTrue(len(self.getProjectJson()) >= 4)

    @patch('client.client_webhook.download_file')
    def test_processWebhookMultipleBooks(self, mock_download_file):
        # given
        client_web_hook = self.setupClientWebhookMock('raw_sources/en-ulb', self.resources_dir, mock_download_file)
        expected_job_count = 4
        expected_error_count = 0

        # when
        results = client_web_hook.process_webhook()

        # then
        self.assertEqual(TestClientWebhook.jobRequestCount, expected_job_count)
        self.assertEqual(len(results['build_logs']), expected_job_count)
        self.assertEqual(len(results['errors']), expected_error_count)
        self.assertTrue('multiple' in results)
        self.assertEqual(results, self.getBuildLogJson())
        self.assertTrue(len(self.getProjectJson()) >= 4)

    @patch('client.client_webhook.download_file')
    def test_processWebhookMultipleBooksErrors(self, mock_download_file):
        # given
        client_web_hook = self.setupClientWebhookMock('raw_sources/en-ulb', self.resources_dir, mock_download_file)
        TestClientWebhook.mock_job_return_value['errors'] = ['error 1','error 2']
        expected_job_count = 4
        expected_error_count = 2 * expected_job_count

        # when
        try:
            client_web_hook.process_webhook()
            captured_error = False
        except:
            captured_error = True

        # then
        self.assertEqual(TestClientWebhook.jobRequestCount, expected_job_count)
        self.assertTrue(captured_error)
        results = self.getBuildLogJson()
        self.assertEqual(len(results['build_logs']), expected_job_count)
        self.assertEqual(len(results['errors']), expected_error_count)
        self.assertTrue('multiple' in results)
        self.assertTrue(len(self.getProjectJson()) >= 4)

    # helpers

    def getBuildLogJson(self):
        return self.readLastUploadedJsonFile('build_log.json')

    def getProjectJson(self):
        return self.readLastUploadedJsonFile('project.json')

    def readLastUploadedJsonFile(self, match):
        json_str = self.readLastUploadedFile(match)
        if json_str:
            json_data = json.loads(json_str)
            return json_data
        return None

    def readLastUploadedFile(self, match):
        file_path = self.get_last_uploaded_file(match)
        if file_path:
            return read_file(file_path)
        return None

    def get_last_uploaded_file(self, match):
        for upload in reversed(TestClientWebhook.uploaded_files):
            if match in upload['key']:
                return upload['file']
        return None

    def setupClientWebhookMock(self, repo_name, base_path, mock_download_file):
        mock_download_file.side_effect = self.mock_download_repo
        source = os.path.join(base_path, repo_name)
        env_vars = self.get_environment(source, base_path)
        self.cwh = ClientWebhook(**env_vars)
        self.cwh.cdn_handler = S3Handler("test_cdn")
        self.cwh.cdn_handler.create_bucket()
        self.cwh.cdn_handler.upload_file = self.mock_cdn_upload_file
        self.cwh.cdn_handler.get_json = self.mock_cdn_get_json
        self.cwh.preconvert_handler = S3Handler("test_preconvert")
        self.cwh.preconvert_handler.create_bucket()
        self.cwh.preconvert_handler.upload_file = self.mock_s3_upload_file
        self.cwh.add_payload_to_tx_converter = self.mock_add_payload_to_tx_converter
        self.cwh.clear_commit_directory_in_cdn = self.mock_clear_commit_directory_in_cdn
        return self.cwh

    @staticmethod
    def mock_download_repo(self, source, target):
        shutil.copyfile(os.path.join(TestClientWebhook.parent_resources_dir, source), target)

    def mock_add_payload_to_tx_converter(self, callback_url, identifier, payload, rc, source_url, tx_manager_job_url):
        TestClientWebhook.jobRequestCount += 1
        mock_job_return_value = TestClientWebhook.mock_job_return_value
        mock_job_return_value['job_id'] = identifier
        return identifier, mock_job_return_value

    def mock_cdn_upload_file(self, project_file, s3_key):
        bucket_name = self.cwh.preconvert_handler.bucket.name
        return self.upload_file(bucket_name, project_file, s3_key)

    def mock_s3_upload_file(self, project_file, s3_key):
        bucket_name = self.cwh.cdn_handler.bucket.name
        return self.upload_file(bucket_name, project_file, s3_key)

    def upload_file(self, bucket_name, project_file, s3_key):
        filename = tempfile.mktemp(dir=TestClientWebhook.base_temp_dir)
        shutil.copyfile(project_file, filename)
        TestClientWebhook.uploaded_files.append({'file': filename, 'key': bucket_name + '/' + s3_key})
        return

    def mock_cdn_get_json(self, project_json_key):
        return {}

    def mock_clear_commit_directory_in_cdn(self, s3_commit_key):
        return

    def get_environment(self, source_path, gogs_url):
        gogs_user_token = 'dummy'
        api_url = 'https://api.door43.org'
        pre_convert_bucket = 'tx-webhook-client'
        cdn_bucket = 'cdn.door43.org'
        base_url = 'https://git.door43.org'
        commit_id = '22f3d09f7a33d2496db6993648f0cd967a9006f6'
        commit_path = '/tx-manager-test-data/en-ulb/commit/22f3d09f7a33d2496db6993648f0cd967a9006f6'
        repo = 'en-ulb'
        user = 'tx-manager-test-data'

        if not source_path:
            source_path = base_url + commit_path

        webhook_data = {
            'after': commit_id,
            'commits': [
                {
                    'id': commit_id,
                    'message': 'Fri Dec 16 2016 11:09:07 GMT+0530 (India Standard Time)\n',
                    'url': source_path,
                }],
            'compare_url': '',
            'repository': {
                'name': repo,
                'owner': {
                    'id': '1234567890',
                    'username': user,
                    'full_name': user,
                    'email': 'you@example.com'
                },
            },
            'pusher': {
                'id': '123456789',
                'username': 'test',
                'full_name': '',
                'email': 'you@example.com'
            },
        }
        env_vars = {
            'api_url': api_url,
            'pre_convert_bucket': pre_convert_bucket,
            'cdn_bucket': cdn_bucket,
            'gogs_url': gogs_url,
            'gogs_user_token': gogs_user_token,
            'commit_data': webhook_data
        }
        return env_vars
