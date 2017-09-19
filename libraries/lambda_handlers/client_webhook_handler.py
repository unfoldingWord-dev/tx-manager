from __future__ import unicode_literals, print_function
import json
from libraries.general_tools.data_utils import json_serial
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
        commit_data = self.retrieve(event, 'data', 'payload')

        # Execute
        return json.dumps(ClientWebhook(commit_data).process_webhook(), default=json_serial)
