from __future__ import unicode_literals, print_function
from libraries.client.client_linter_callback import ClientLinterCallback
from libraries.lambda_handlers.handler import Handler


class ClientLinterCallbackHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        identifier = self.retrieve(self.data, 'identifier', 'Payload')
        success = self.retrieve(self.data, 'success', 'Payload', required=False, default=False)
        warnings = self.retrieve(self.data, 'warnings', 'Payload', required=False, default=[])

        # Execute
        return ClientLinterCallback(identifier, success, warnings).process_callback()
