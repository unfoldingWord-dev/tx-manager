from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.client_callback_handler import ClientCallbackHandler


class TestClientCallbackHandler(TestCase):

    @mock.patch('libraries.client.client_callback.ClientCallback.process_callback')
    def test_handle(self, mock_process_callback):
        mock_process_callback.return_value = None
        event = {
            'data': {},
        }
        handler = ClientCallbackHandler()
        self.assertIsNone(handler.handle(event, None))
