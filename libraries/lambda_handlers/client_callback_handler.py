from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler
from libraries.client.client_callback import ClientCallback
from libraries.app.app import App


class ClientCallbackHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Execute
        return ClientCallback(self.data).process_callback()
