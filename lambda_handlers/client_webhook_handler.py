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
        env_vars = self.retrieve(event, 'vars', 'payload')
        # Perform checks that we have these vars:
        self.retrieve(env_vars, 'api_url', 'Environment Vars')
        self.retrieve(env_vars, 'pre_convert_bucket', 'Environment Vars')
        self.retrieve(env_vars, 'cdn_bucket', 'Environment Vars')
        self.retrieve(env_vars, 'gogs_url', 'Environment Vars')
        self.retrieve(env_vars, 'gogs_user_token', 'Environment Vars')
        # Make the commit data a var in vars
        env_vars['commit_data'] = self.retrieve(event, 'data', 'payload')
        return ClientWebhook(**env_vars).process_webhook()
