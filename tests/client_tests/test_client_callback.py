from __future__ import absolute_import, unicode_literals, print_function

import json
import tempfile

import os
import mock
import shutil

from general_tools import file_utils
from mock import patch
from unittest import TestCase
from client.client_callback import ClientCallback


class TestClientCallback(TestCase):
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'tx-manager')
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    source_zip = ''
    build_log_json = ''
    project_json = ''
    uploaded_files = []

    def setUp(self):
        try:
            os.makedirs(TestClientCallback.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=TestClientCallback.base_temp_dir, prefix='callbackTest_')
        TestClientCallback.uploaded_files = []


    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)


    def test_client_callback(self):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        mock_ccb = self.mockClientCallback()

        #when
        results = mock_ccb.process_callback()

        #then
        self.assertIsNotNone(results)

    # @patch('client.client_callback.ClientCallback.download_file')
    # def test_client_callback_multiple(self):
    #     mock_download_file.side_effect = self.mock_download_repo
    #     cwh = ClientCallbackHandler()
    #     event = {
    #         'data': {},
    #         'body-json': {
    #             'identifier' : 'tx-manager-test-data/en-ulb/22f3d09f7a/4/0',
    #             'output' : 'https://test-cdn.door43.org/tx/job/6864ae1b91195f261ba5cda62d58d5ad9333f3131c787bb68f20c27adcc85cad.zip'
    #         },
    #         'vars': {
    #             'gogs_url': 'https://git.example.com',
    #             'cdn_url': 'https://cdn.example.com',
    #             'api_url': 'https://api.example.com',
    #             'cdn_bucket': 'cdn_test_bucket'
    #         }
    #     }
    #     cwh.handle(event, None)


        # helpers

    def mockClientCallback(self):
        self.build_log_json = '{}'
        self.project_json = '{}'

        vars = {
            'job_data': {
                'identifier': 'tx-manager-test-data/en-ulb/22f3d09f7a',
                'output' : 'https://test-cdn.door43.org/tx/job/6864ae1b91195f261ba5cda62d58d5ad9333f3131c787bb68f20c27adcc85cad.zip'
            },
            'gogs_url': 'https://git.example.com',
            'cdn_bucket': 'cdn_test_bucket'
        }
        mock_ccb = ClientCallback(**vars)
        mock_ccb.downloadFile = self.mock_downloadFile
        mock_ccb.cdnUploadFile = self.mock_cdnUploadFile
        mock_ccb.cdnGetJsonFile = self.mock_cdnGetJsonFile
        return mock_ccb

    def mock_downloadFile(self, target, url):
        fileName = os.path.basename(url)
        if '.zip' in fileName:
            shutil.copyfile(self.source_zip, target)
        elif fileName == 'build_log.json':
            file_utils.write_file(target, self.build_log_json)
        elif fileName == 'project.json':
            file_utils.write_file(target, self.project_json)

    def mock_cdnUploadFile(self, cdn_handler, project_file, s3_key, cache_time=600):
        bucket_name = cdn_handler.bucket.name
        TestClientCallback.uploaded_files.append({ 'file' : project_file, 'key' : bucket_name + '/' + s3_key})
        return

    def mock_cdnGetJsonFile(self, cdn_handler, s3_key):
        if 'build_log.json' in s3_key:
            return json.loads(self.build_log_json)
        elif 'project.json' in s3_key:
            return json.loads(self.project_json)
        return ''
