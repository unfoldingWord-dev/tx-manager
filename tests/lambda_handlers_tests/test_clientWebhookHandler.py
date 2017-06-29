from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.client_webhook_handler import ClientWebhookHandler


class TestClientWebhookHandler(TestCase):

    @mock.patch('client.client_webhook.ClientWebhook.process_webhook')
    def test_handle(self, mock_process_webhook):
        mock_process_webhook.return_value = None
        event = {
            'data': {},
            'body-json': {
                'commit_id': '123456890',
            },
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.example.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket',
                'pre_convert_bucket': 'pre_convert_bucket',
                'gogs_user_token': 'token1'
            }
        }
        handler = ClientWebhookHandler()
        self.assertIsNone(handler.handle(event, None))
