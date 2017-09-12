from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler
from libraries.client.client_webhook import ClientWebhook


class ClientWebhookHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        commit_data = self.retrieve(event, 'data', 'payload'),

        # Execute
        return ClientWebhook(commit_data).process_webhook()
