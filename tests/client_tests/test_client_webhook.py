from __future__ import absolute_import, unicode_literals, print_function
import json
import os
import shutil
import tempfile
import unittest
import hashlib
import boto3
from libraries.aws_tools.s3_handler import S3Handler
from mock import patch
from libraries.client.client_webhook import ClientWebhook
from libraries.door43_tools.linter_messaging import LinterMessaging
from libraries.general_tools.file_utils import read_file
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.models.manifest import TxManifest
from libraries.models.job import TxJob
from moto import mock_s3, mock_dynamodb2, mock_sqs
from libraries.db.db import DB


@mock_s3
@mock_dynamodb2
@mock_sqs
class TestClientWebhook(unittest.TestCase):
    MANIFEST_TABLE_NAME = 'client-webhook-test-manifest'
    JOB_TABLE_NAME = 'client-webhook-test-job'
    LINTER_MESSAGING_NAME = 'dummy_linter_messaging'
    parent_resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    temp_dir = None
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'test-tx-manager')
    default_mock_job_return_value = TxJob({
        'job_id': '0',
        'status': 'started',
        'success': 'success',
        'resource_type': 'obs',
        'input_format': 'md',
        'output_format': 'html',
        'convert_module': 'module1',
        'created_at': '2017-05-22T13:39:15Z',
        'errors': []
    })
    mock_job_return_value = default_mock_job_return_value
    setup_table = False

    def setUp(self):
        try:
            os.makedirs(TestClientWebhook.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='webhookTest_')
        self.job_request_count = 0
        self.linter_success = True
        self.linter_warnings = []

        # copy the job object
        TestClientWebhook.mock_job_return_value = TxJob(self.default_mock_job_return_value.get_db_data())
        self.uploaded_files = []
        self.job_db_handler = DynamoDBHandler(self.JOB_TABLE_NAME)
        if not TestClientWebhook.setup_table:
            self.init_tables()
            TestClientWebhook.setup_table = True

    def tearDown(self):
        shutil.rmtree(TestClientWebhook.base_temp_dir, ignore_errors=True)

    def init_tables(self):
        try:
            self.job_db_handler.table.delete()
        except:
            pass
        self.job_db_handler.resource.create_table(
            TableName=self.JOB_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'job_id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'job_id',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )

        DB(connection_string='sqlite:///:memory:', default_db=True)

    @patch('libraries.client.client_webhook.download_file')
    def test_download_repo(self, mock_download_file):
        mock_download_file.side_effect = self.mock_download_repo
        cwh = ClientWebhook()
        try:
            os.makedirs(cwh.base_temp_dir)
        except:
            pass
        cwh.download_repo('bible_bundle_master', TestClientWebhook.base_temp_dir)

    @patch('libraries.client.client_webhook.download_file')
    @patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhook(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        mock_send_payload_to_run_linter.return_value = {'success': True, 'warnings': []}
        client_web_hook = self.setupClientWebhookMock('kpb_mat_text_udb_repo', self.parent_resources_dir,
                                                      mock_download_file)
        expected_job_count = 1
        expected_error_count = 0

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults(results, expected_job_count, expected_error_count)

        # Check repo was added to manifest table
        repo_name = client_web_hook.commit_data['repository']['name']
        user_name = client_web_hook.commit_data['repository']['owner']['username']
        tx_manifest = DB.session.query(TxManifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        self.assertEqual(tx_manifest.repo_name, client_web_hook.commit_data['repository']['name'])
        self.assertEqual(tx_manifest.resource_id, 'udb')
        self.assertEqual(tx_manifest.lang_code, 'kpb')

    @patch('libraries.client.client_webhook.download_file')
    @patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookError(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        mock_send_payload_to_run_linter.return_value = {'success': True, 'warnings': []}
        client_web_hook = self.setupClientWebhookMock('kpb_mat_text_udb_repo', self.parent_resources_dir,
                                                      mock_download_file)
        TestClientWebhook.mock_job_return_value.errors = ['error 1', 'error 2']
        expected_job_count = 1
        expected_error_count = 2

        # when
        try:
            client_web_hook.process_webhook()
        except:
            pass

        # then
        self.validateResults(self.getBuildLogJson(), expected_job_count, expected_error_count)

    @patch('libraries.client.client_webhook.download_file')
    @patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookMultipleBooks(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        self.setup_linter()
        self.linter_success = True
        self.linter_warnings = []
        mock_send_payload_to_run_linter.side_effect = self.mock_send_payload_to_run_linter
        client_web_hook = self.setupClientWebhookMock(os.path.join('raw_sources', 'en-ulb'),
                                                      self.resources_dir, mock_download_file)
        expected_job_count = 4
        expected_error_count = 0
        expected_warnings_count = expected_job_count * len(self.linter_warnings)

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults2(results, expected_job_count, expected_error_count, expected_warnings_count)

    @patch('libraries.client.client_webhook.download_file')
    @patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookMultipleBooksWarnings(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        self.setup_linter()
        self.linter_success = True
        self.linter_warnings = ["warning!!"]
        mock_send_payload_to_run_linter.side_effect = self.mock_send_payload_to_run_linter
        client_web_hook = self.setupClientWebhookMock(os.path.join('raw_sources', 'en-ulb'),
                                                      self.resources_dir, mock_download_file)
        expected_job_count = 4
        expected_error_count = 0
        expected_warnings_count = expected_job_count * len(self.linter_warnings)

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults2(results, expected_job_count, expected_error_count, expected_warnings_count)

    @patch('libraries.client.client_webhook.download_file')
    @patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookMultipleBooksLinterFail(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        self.setup_linter()
        self.linter_success = False
        self.linter_warnings = []
        mock_send_payload_to_run_linter.side_effect = self.mock_send_payload_to_run_linter
        client_web_hook = self.setupClientWebhookMock(os.path.join('raw_sources', 'en-ulb'),
                                                      self.resources_dir, mock_download_file)
        expected_job_count = 4
        expected_error_count = 0
        expected_warnings_count = expected_job_count

        # when
        results = client_web_hook.process_webhook()

        # then
        self.validateResults2(results, expected_job_count, expected_error_count, expected_warnings_count)

    @patch('libraries.client.client_webhook.download_file')
    @patch('libraries.client.client_webhook.ClientWebhook.send_payload_to_run_linter')
    def test_processWebhookMultipleBooksErrors(self, mock_send_payload_to_run_linter, mock_download_file):
        # given
        client_web_hook = self.setupClientWebhookMock(os.path.join('raw_sources', 'en-ulb'), self.resources_dir,
                                                      mock_download_file)
        self.setup_linter()
        self.linter_success = True
        self.linter_warnings = ["warning!!"]
        mock_send_payload_to_run_linter.side_effect = self.mock_send_payload_to_run_linter
        TestClientWebhook.mock_job_return_value.errors = ['error 1', 'error 2']
        expected_job_count = 4
        expected_error_count = 2 * expected_job_count
        expected_warnings_count = expected_job_count * len(self.linter_warnings)

        # when
        try:
            client_web_hook.process_webhook()
            captured_error = False
        except:
            captured_error = True

        # then
        self.assertTrue(captured_error)
        self.validateResults2(self.getBuildLogJson(), expected_job_count, expected_error_count, expected_warnings_count)

    #
    # helpers
    #

    def validateResults2(self, results, expected_job_count, expected_error_count, expected_warnings_count):
        self.assertEqual(len(results['warnings']), expected_warnings_count)
        self. validateResults(results, expected_job_count, expected_error_count)

    def validateResults(self, results, expected_job_count, expected_error_count):
        multipleJob = expected_job_count > 1
        self.assertEqual(self.job_request_count, expected_job_count)
        self.assertTrue(len(results['job_id']) > 16)
        self.assertTrue(len(results['commit_id']) > 8)
        self.assertTrue(len(results['repo_owner']) > 1)
        self.assertTrue(len(results['repo_name']) > 1)
        if multipleJob:
            self.assertEqual(len(results['build_logs']), expected_job_count)
            self.assertTrue(len(results['source']) > 1)
        self.assertEqual(len(results['errors']), expected_error_count)
        self.assertEqual(multipleJob, 'multiple' in results)
        self.assertDictEqual(results, self.getBuildLogJson())
        self.assertTrue(len(self.getProjectJson()) >= 4)

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
        for upload in reversed(self.uploaded_files):
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

    def mock_download_repo(self, source, target):
        if source != target:
            shutil.copyfile(os.path.join(TestClientWebhook.parent_resources_dir, source), target)

    def mock_add_payload_to_tx_converter(self, callback_url, identifier, payload, rc, source_url, tx_manager_job_url):
        self.job_request_count += 1
        mock_job_return_value = TestClientWebhook.mock_job_return_value
        mock_job_return_value.job_id = hashlib.sha256().hexdigest()
        mock_job_return_value.db_handler = self.job_db_handler
        mock_job_return_value.source = payload['source']
        mock_job_return_value.insert()
        return identifier, mock_job_return_value

    def mock_send_payload_to_run_linter(self, payload, async=False):
        data = payload['data']
        source_url = data['source_url']
        ret_value = {
            'success': self.linter_success,
            'warnings': self.linter_warnings
        }
        if 'linter_messaging_name' in data:
            message_queue = LinterMessaging(data['linter_messaging_name'])
            message_queue.notify_lint_job_complete(source_url, self.linter_success, payload=ret_value)

        return ret_value

    def mock_cdn_upload_file(self, project_file, s3_key):
        bucket_name = self.cwh.preconvert_handler.bucket.name
        return self.upload_file(bucket_name, project_file, s3_key)

    def mock_s3_upload_file(self, project_file, s3_key):
        bucket_name = self.cwh.cdn_handler.bucket.name
        return self.upload_file(bucket_name, project_file, s3_key)

    def upload_file(self, bucket_name, project_file, s3_key):
        filename = tempfile.mktemp(dir=TestClientWebhook.base_temp_dir)
        shutil.copyfile(project_file, filename)
        self.uploaded_files.append({'file': filename, 'key': bucket_name + '/' + s3_key})
        return

    def mock_cdn_get_json(self, project_json_key):
        return {}

    def mock_clear_commit_directory_in_cdn(self, s3_commit_key):
        return

    def setup_linter(self):
        try:
            #setup linter messaging
            sqs = boto3.resource('sqs')
            queue = sqs.create_queue(QueueName=TestClientWebhook.LINTER_MESSAGING_NAME, Attributes={'DelaySeconds': '5'})
        except Exception as e:
            pass

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
        manifest_table_name = TestClientWebhook.MANIFEST_TABLE_NAME
        job_table_name = TestClientWebhook.JOB_TABLE_NAME
        linter_messaging_name = TestClientWebhook.LINTER_MESSAGING_NAME

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
            'commit_data': webhook_data,
            'manifest_table_name': manifest_table_name,
            'linter_messaging_name': linter_messaging_name,
            'job_table_name': job_table_name
        }
        return env_vars
