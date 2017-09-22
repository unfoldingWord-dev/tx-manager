from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.register_module_handler import RegisterModuleHandler
from libraries.models.module import TxModule


class TestRegisterModuleHandler(TestCase):

    @mock.patch('libraries.manager.manager.TxManager.register_module')
    def test_handle(self, mock_register_module):
        mock_register_module.return_value = TxModule()
        event = {
            'data': {
                "name": "tx-md2html_convert",
                "version": "1",
                "type": "conversion",
                "resource_types": ["obs"],
                "input_format": ["md"],
                "output_format": ["html"],
                "options": {'pageSize': 'A4'},
                "private_links": [],
                "public_links": []
            }
        }
        handler = RegisterModuleHandler()
        self.assertIsInstance(handler.handle(event, None), dict)
