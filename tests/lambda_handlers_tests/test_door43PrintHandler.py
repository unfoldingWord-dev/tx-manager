from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.door43_print_handler import Door43PrintHandler


class TestDoor43PrintHandler(TestCase):

    @mock.patch('libraries.door43_tools.project_printer.ProjectPrinter.print_project')
    def test_handle(self, mock_print_project):
        mock_print_project.return_value = None
        event = {
            'data': {
                'id': 'door43/en_obs/12345'
            }
        }
        handler = Door43PrintHandler()
        self.assertIsNone(handler.handle(event, None))
