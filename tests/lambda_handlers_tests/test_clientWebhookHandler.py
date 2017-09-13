from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.client_webhook_handler import ClientWebhookHandler


class TestClientWebhookHandler(TestCase):

    @mock.patch('libraries.client.client_webhook.ClientWebhook.process_webhook')
    def test_handle(self, mock_process_webhook):
        mock_process_webhook.return_value = None
        event = {
            'data': {
                'commit_id': '123456890',
            }
        }
        handler = ClientWebhookHandler()
        self.assertIsNone(handler.handle(event, None))
