from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler
from libraries.client.client_converter_callback import ClientConverterCallback


class ClientConverterCallbackHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Execute
        return ClientConverterCallback(**self.data).process_converter_callback()
