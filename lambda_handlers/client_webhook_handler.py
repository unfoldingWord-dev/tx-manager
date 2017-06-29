from __future__ import unicode_literals, print_function
from lambda_handlers.handler import Handler
from client.client_webhook import ClientWebhook


class ClientWebhookHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        data = {}
        if 'data' in event and isinstance(event['data'], dict):
            data = event['data']
        if 'body-json' in event and isinstance(event['body-json'], dict):
            data.update(event['body-json'])
        # Set required env_vars
        env_vars = {
            'api_url': self.retrieve(event['vars'], 'api_url', 'Environment Vars'),
            'pre_convert_bucket': self.retrieve(event['vars'], 'pre_convert_bucket', 'Environment Vars'),
            'cdn_bucket': self.retrieve(event['vars'], 'cdn_bucket', 'Environment Vars'),
            'gogs_url': self.retrieve(event['vars'], 'gogs_url', 'Environment Vars'),
            'gogs_user_token': self.retrieve(event['vars'], 'gogs_user_token', 'Environment Vars'),
            'commit_data': self.retrieve(event, 'data', 'payload')
        }
        return ClientWebhook(**env_vars).process_webhook()
