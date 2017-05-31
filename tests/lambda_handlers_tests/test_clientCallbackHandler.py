from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.client_callback_handler import ClientCallbackHandler


class TestClientCallbackHandler(TestCase):

    @mock.patch('client.client_callback.ClientCallback.process_callback')
    def test_handle(self, mock_process_callback):
        mock_process_callback.return_value = None
        event = {
            'data': {},
            'body-json': {
                'job_id': '1'
            },
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.example.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket'
            }
        }
        handler = ClientCallbackHandler()
        self.assertIsNone(handler.handle(event, None))
