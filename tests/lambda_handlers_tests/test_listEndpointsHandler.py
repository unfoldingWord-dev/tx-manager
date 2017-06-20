from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.list_endpoints_handler import ListEndpointsHandler


class TestListEndpointsHandler(TestCase):

    @mock.patch('libraries.manager.manager.TxManager.setup_resources')
    @mock.patch('libraries.manager.manager.TxManager.list_endpoints')
    def test_handle(self, mock_list_endpoints, mock_setup_resources):
        mock_list_endpoints.return_value = None
        event = {
            'data': {},
            'body-json': {},
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.example.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket',
                'job_table_name': 'test-tx-job',
                'module_table_name': 'test-tx-module'
            }
        }
        handler = ListEndpointsHandler()
        self.assertIsNone(handler.handle(event, None))
