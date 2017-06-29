from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.door43_print_handler import Door43PrintHandler


class TestDoor43PrintHandler(TestCase):

    @mock.patch('door43_tools.project_printer.ProjectPrinter.print_project')
    def test_handle(self, mock_print_project):
        mock_print_project.return_value = None
        event = {
            'data': {},
            'body-json': {
                'id': 'door43/en_obs/12345'
            },
            'vars': {
                'cdn_url': 'https://cdn.example.com',
                'cdn_bucket': 'cdn_test_bucket',
            }
        }
        handler = Door43PrintHandler()
        self.assertIsNone(handler.handle(event, None))
