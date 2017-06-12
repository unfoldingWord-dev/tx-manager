from __future__ import absolute_import, unicode_literals, print_function

import tempfile

import os

import mock
import shutil
from mock import patch
from unittest import TestCase
from lambda_handlers.client_callback_handler import ClientCallbackHandler


class TestClientCallbackHandler(TestCase):
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'tx-manager')

    def setUp(self):
        try:
            os.makedirs(TestClientCallbackHandler.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=TestClientCallbackHandler.base_temp_dir, prefix='callbackTest_')

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)


    @mock.patch('client.client_callback.ClientCallback.process_callback')
    def test_handle(self, mock_process_callback):
        mock_process_callback.return_value = None
        event = {
            'data': {},
            'body-json': {
                'job_id': '1'
            },
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.example.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket'
            }
        }
        handler = ClientCallbackHandler()
        self.assertIsNone(handler.handle(event, None))

    @patch('client.client_webhook.download_file')
    def test_client_callback(self, mock_download_file):
        mock_download_file.side_effect = self.mock_download_repo
        cwh = ClientCallbackHandler()
        event = {
            'data': {},
            'body-json': {
                'identifier': 'tx-manager-test-data/en-ulb/22f3d09f7a'
            },
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.example.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket'
            }
        }
        results = cwh.handle(event, None)
        self.assertIsNotNone(results)

    @patch('client.client_webhook.download_file')
    def test_client_callback_multiple(self, mock_download_file):
        mock_download_file.side_effect = self.mock_download_repo
        cwh = ClientCallbackHandler()
        event = {
            'data': {},
            'body-json': {
                'identifier': 'tx-manager-test-data/en-ulb/22f3d09f7a/4/0'
            },
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.example.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket'
            }
        }
        cwh.handle(event, None)


        # helpers

    def mock_download_repo(source, target):
        shutil.copyfile(os.path.join(TestClientCallbackHandler.parent_resources_dir, source), target)

