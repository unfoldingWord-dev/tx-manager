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
        vars = self.retrieve(event, 'vars', 'payload')
        # Perform checks that we have these vars:
        self.retrieve(vars, 'api_url', 'Environment Vars')
        self.retrieve(vars, 'pre_convert_bucket', 'Environment Vars')
        self.retrieve(vars, 'cdn_bucket', 'Environment Vars')
        self.retrieve(vars, 'gogs_url', 'Environment Vars')
        self.retrieve(vars, 'gogs_user_token', 'Environment Vars')
        # Make the commit data a var in vars
        vars['commit_data'] = self.retrieve(event, 'data', 'payload')
        return ClientWebhook(**vars).process_webhook()
