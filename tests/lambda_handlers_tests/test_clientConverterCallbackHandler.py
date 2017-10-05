from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from moto import mock_s3
from libraries.lambda_handlers.client_converter_callback_handler import ClientConverterCallbackHandler


@mock_s3
class TestClientConverterCallbackHandler(TestCase):

    @mock.patch('libraries.client.client_converter_callback.ClientConverterCallback.process_callback')
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
        handler = ClientConverterCallbackHandler()
        self.assertIsNone(handler.handle(event, None))

    @mock.patch('libraries.client.client_linter_callback.ClientLinterCallback.process_callback')
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
        handler = ClientConverterCallbackHandler()
        had_exception = False
        try:
            results = handler.handle(event, None)
        except Exception as e:
            had_exception = True

        self.assertTrue(had_exception)
