from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from moto import mock_s3

from libraries.app.app import App
from libraries.lambda_handlers.client_linter_callback_handler import ClientLinterCallbackHandler


@mock_s3
class TestClientLinterCallbackHandler(TestCase):

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        App.cdn_s3_handler().create_bucket()

    @mock.patch('libraries.linters.client_linter_callback.ClientLinterCallback.process_callback')
    def test_handle(self, mock_process_callback):
        mock_process_callback.return_value = None
        event = {
            'data': {
                'identifier': 'dummy_id',
                's3_results_key': 'results',
                'success': True,
                'info': [],
                'warnings': [],
                'errors': []
            },
        }
        handler = ClientLinterCallbackHandler()
        self.assertIsNone(handler.handle(event, None))

    @mock.patch('libraries.linters.client_linter_callback.ClientLinterCallback.process_callback')
    def test_handle_no_id(self, mock_process_callback):
        mock_process_callback.return_value = None
        event = {
            'data': {
                's3_results_key': 'results',
                'success': True,
                'info': [],
                'warnings': [],
                'errors': []
            },
        }
        handler = ClientLinterCallbackHandler()
        had_exception = False
        try:
            results = handler.handle(event, None)
        except Exception as e:
            had_exception = True

        self.assertTrue(had_exception)
