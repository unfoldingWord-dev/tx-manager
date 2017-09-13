from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.register_module_handler import RegisterModuleHandler


class TestRegisterModuleHandler(TestCase):

    @mock.patch('libraries.manager.manager.TxManager.register_module')
    def test_handle(self, mock_register_module):
        mock_register_module.return_value = None
        event = {
            'data': {
                "name": "tx-md2html_convert",
                "version": "1",
                "type": "conversion",
                "resource_types": ["obs"],
                "input_format": ["md"],
                "output_format": ["html"],
                "options": [],
                "private_links": [],
                "public_links": []
            }
        }
        handler = RegisterModuleHandler()
        self.assertIsNone(handler.handle(event, None))
