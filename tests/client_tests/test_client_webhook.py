from __future__ import absolute_import, unicode_literals, print_function
import os
import shutil
import tempfile
import unittest
from mock import patch
from client.client_webhook import ClientWebhook


class TestClientWebhook(unittest.TestCase):
    resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
    temp_dir = None
    print(resources_dir)

    base_temp_dir = os.path.join(tempfile.gettempdir(), 'tx-manager')
    shutil.rmtree(base_temp_dir, ignore_errors=True)

    @staticmethod
    def mock_download_repo(source, target):
        print('Mock downloading {}'.format(source), end=' ')
        shutil.copyfile(os.path.join(TestClientWebhook.resources_dir, source), target)
        print('finished.')

    def setUp(self):
        try:
            os.makedirs(TestClientWebhook.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=TestClientWebhook.base_temp_dir, prefix='webhookTest_')

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('client.client_webhook.download_file')
    def test_download_repo(self, mock_download_file):

        mock_download_file.side_effect = self.mock_download_repo
        cwh = ClientWebhook()
        #cwh.download_repo('bible_bundle_master', self.temp_dir)
        cwh.download_repo('bible_bundle_master', TestClientWebhook.base_temp_dir)
