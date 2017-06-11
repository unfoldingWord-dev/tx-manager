from __future__ import absolute_import, unicode_literals, print_function
import json
import os
import shutil
import tempfile
import unittest
from mock import patch
from client.client_webhook import ClientWebhook
from general_tools.file_utils import read_file

class TestClientWebhook(unittest.TestCase):
    parent_resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    temp_dir = None
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'tx-manager')
    shutil.rmtree(base_temp_dir, ignore_errors=True)
    jobRequestCount = 0
    default_mock_job_return_value = {'job_id': '0', 'status': 'started', 'success': 'success', 'resource_type': 'obs',
                             'input_format': 'md', 'output_format': 'html', 'convert_module': 'module1',
                             'created_at': '2017-05-22T13:39:15Z', 'errors': []}
    mock_job_return_value = default_mock_job_return_value
    uploaded_files = []
    uploaded_keys = []

    def setUp(self):
        try:
            os.makedirs(TestClientWebhook.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=TestClientWebhook.base_temp_dir, prefix='webhookTest_')
        TestClientWebhook.jobRequestCount = 0
        TestClientWebhook.mock_job_return_value = json.loads(json.dumps(TestClientWebhook.default_mock_job_return_value)) # do deep copy
        TestClientWebhook.uploaded_files = []
        TestClientWebhook.uploaded_keys = []

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('client.client_webhook.download_file')
    def test_download_repo(self, mock_download_file):
        mock_download_file.side_effect = self.mock_download_repo
        cwh = ClientWebhook()
        cwh.download_repo('bible_bundle_master', TestClientWebhook.base_temp_dir)

    @patch('client.client_webhook.download_file')
    def test_process_webhook(self, mock_download_file):
        # given
        mock_download_file.side_effect = self.mock_download_repo
        clientWebHook = self.setupClientWebhookMock('kpb_mat_text_udb_repo', self.parent_resources_dir)
        expectedJobCount = 1
        expectedJobID = 'job_1'
        expectedErrorCount = 0

        # when
        results = clientWebHook.process_webhook()

        # then
        self.assertEqual(TestClientWebhook.jobRequestCount, expectedJobCount)
        self.assertEqual(results['job_id'], expectedJobID)
        self.assertFalse('multiple' in results)
        self.assertEqual(len(results['errors']), expectedErrorCount)
        self.assertEqual(results, self.getLastJson())

    @patch('client.client_webhook.download_file')
    def test_process_webhook_error(self, mock_download_file):
        # given
        mock_download_file.side_effect = self.mock_download_repo
        clientWebHook = self.setupClientWebhookMock('kpb_mat_text_udb_repo', self.parent_resources_dir)
        TestClientWebhook.mock_job_return_value['errors'] = ['error 1','error 2']
        expectedJobCount = 1
        expectedJobID = 'job_1'
        capturedError = False
        expectedErrorCount = 2

        # when
        try:
            clientWebHook.process_webhook()
        except:
            capturedError = True

        # then
        self.assertEqual(TestClientWebhook.jobRequestCount, expectedJobCount)
        self.assertTrue(capturedError)
        results = self.getLastJson()
        self.assertEqual(results['job_id'], expectedJobID)
        self.assertFalse('multiple' in results)
        self.assertEqual(len(results['errors']), expectedErrorCount)

    @patch('client.client_webhook.download_file')
    def test_process_webhook_multiple_books(self, mock_download_file):
        # given
        mock_download_file.side_effect = self.mock_download_repo
        clientWebHook = self.setupClientWebhookMock('raw_sources/en-ulb', self.resources_dir)
        expectedJobCount = 4
        expectedErrorCount = 0

        # when
        results = clientWebHook.process_webhook()

        # then
        self.assertEqual(TestClientWebhook.jobRequestCount, expectedJobCount)
        self.assertEqual(len(results['build_logs']), expectedJobCount)
        self.assertEqual(len(results['errors']), expectedErrorCount)
        self.assertTrue('multiple' in results)
        self.assertEqual(results, self.getLastJson())

    @patch('client.client_webhook.download_file')
    def test_process_webhook_multiple_books_errors(self, mock_download_file):
        # given
        mock_download_file.side_effect = self.mock_download_repo
        clientWebHook = self.setupClientWebhookMock('raw_sources/en-ulb', self.resources_dir)
        TestClientWebhook.mock_job_return_value['errors'] = ['error 1','error 2']
        expectedJobCount = 4
        expectedErrorCount = 2 * expectedJobCount

        # when
        try:
            clientWebHook.process_webhook()
        except:
            capturedError = True

        # then
        self.assertEqual(TestClientWebhook.jobRequestCount, expectedJobCount)
        self.assertTrue(capturedError)
        results = self.getLastJson()
        self.assertEqual(len(results['build_logs']), expectedJobCount)
        self.assertEqual(len(results['errors']), expectedErrorCount)
        self.assertTrue('multiple' in results)

    # helpers

    def getLastJson(self):
        jsonFile = TestClientWebhook.uploaded_files[-1]
        text = read_file(jsonFile)
        return json.loads(text)

    @staticmethod
    def mock_download_repo(source, target):
        shutil.copyfile(os.path.join(TestClientWebhook.parent_resources_dir, source), target)

    def mock_sendPayloadToTxConverter(self, callback_url, identifier, payload, rc, source_url, tx_manager_job_url):
        TestClientWebhook.jobRequestCount += 1
        job_id = "job_" + str(TestClientWebhook.jobRequestCount)
        mock_job_return_value = TestClientWebhook.mock_job_return_value
        mock_job_return_value['job_id'] = job_id
        return job_id, mock_job_return_value

    def mock_cdnUploadFile(self, cdn_handler, project_file, s3_key):
        TestClientWebhook.uploaded_files.append(project_file)
        TestClientWebhook.uploaded_keys.append(s3_key)
        return

    def mock_cdnGetJson(self, cdn_handler, project_json_key):
        return { }

    def mock_cdnDeleteFile(self, cdn_handler, obj):
        return

    def setupClientWebhookMock(self, repoName, basePath):
        source = os.path.join(basePath, repoName)
        env_vars = self.getEnvironment(source, basePath)
        cwh = ClientWebhook(**env_vars)
        cwh.sendPayloadToTxConverter = self.mock_sendPayloadToTxConverter
        cwh.cdnUploadFile = self.mock_cdnUploadFile
        cwh.cdnGetJson = self.mock_cdnGetJson
        cwh.cdnDeleteFile = self.mock_cdnDeleteFile
        return cwh

    def getEnvironment(self, sourcePath, gogsUrl):
        gogsUserToken = 'dummy'
        api_url = 'https://api.door43.org'
        pre_convert_bucket = 'tx-webhook-client'
        gogs_url = 'https://git.door43.org'
        cdn_bucket = 'cdn.door43.org'
        baseUrl = 'https://git.door43.org'
        commitID = '22f3d09f7a33d2496db6993648f0cd967a9006f6'
        commitPath = '/tx-manager-test-data/en-ulb/commit/22f3d09f7a33d2496db6993648f0cd967a9006f6'
        repo = 'en-ulb'
        user = 'tx-manager-test-data'

        if not sourcePath:
            sourcePath = baseUrl + commitPath

        webhookData = {
            'after': commitID,
            'commits': [
                {
                    'id': commitID,
                    'message': 'Fri Dec 16 2016 11:09:07 GMT+0530 (India Standard Time)\n',
                    'url': sourcePath,
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
            'gogs_url': gogsUrl,
            'gogs_user_token': gogsUserToken,
            'commit_data': webhookData
        }
        return env_vars
