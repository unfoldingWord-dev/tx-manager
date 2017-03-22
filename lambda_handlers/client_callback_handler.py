from __future__ import unicode_literals, print_function
from lambda_handlers.handler import Handler
from client.client_callback import ClientCallback


class ClientCallbackHandler(Handler):

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
            'cdn_bucket': self.retrieve(event['vars'], 'cdn_bucket', 'Environment Vars'),
            'gogs_url': self.retrieve(event['vars'], 'gogs_url', 'Environment Vars'),
            'job_data': self.retrieve(event, 'data', 'payload')
        }
        return ClientCallback(**env_vars).process_callback()
