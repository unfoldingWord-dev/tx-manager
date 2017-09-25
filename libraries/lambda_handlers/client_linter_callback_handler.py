from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler
from libraries.linters.linter_callback import ClientLinterCallback


class ClientLinterCallbackHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Execute
        return ClientLinterCallback(**self.data).process_converter_callback()