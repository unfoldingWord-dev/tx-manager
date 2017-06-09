from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.register_module_handler import RegisterModuleHandler


class TestRegisterModuleHandler(TestCase):

    @mock.patch('manager.manager.TxManager.setup_resources')
    @mock.patch('manager.manager.TxManager.register_module')
    def test_handle(self, mock_register_module, mock_setup_resources):
        mock_register_module.return_value = None
        event = {
            'data': {},
            'body-json': {
                    "name": "tx-md2html_convert",
                    "version": "1",
                    "type": "conversion",
                    "resource_types": ["obs"],
                    "input_format": ["md"],
                    "output_format": ["html"],
                    "options": [],
                    "private_links": [],
                    "public_links": []
            },
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.example.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket',
                'job_table_name': 'test-tx-job',
                'module_table_name': 'test-tx-module'
            }
        }
        handler = RegisterModuleHandler()
        self.assertIsNone(handler.handle(event, None))
