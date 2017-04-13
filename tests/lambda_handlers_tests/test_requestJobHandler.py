from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.request_job_handler import RequestJobHandler


class TestRequestJobHandler(TestCase):

    @mock.patch('manager.manager.TxManager.setup_resources')
    @mock.patch('manager.manager.TxManager.setup_job')
    def test_handle(self, mock_setup_job, mock_setup_resources):
        mock_setup_job.return_value = None
        event = {
            'data': {},
            'body-json': {
                "gogs_user_token": "token1",
                "cdn_bucket": "test_cdn_bucket",
                "source": "test_source",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "hstml"
            },
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.exmaple.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket',
                'job_table_name': 'test-tx-job',
                'module_table_name': 'test-tx-module'
            }
        }
        handler = RequestJobHandler()
        self.assertIsNone(handler.handle(event, None))
