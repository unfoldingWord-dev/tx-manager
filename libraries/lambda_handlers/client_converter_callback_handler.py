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
        # Gather arguments
        identifier = self.retrieve(self.data, 'identifier', 'Payload')
        success = self.retrieve(self.data, 'success', 'Payload', required=False, default=False)
        info = self.retrieve(self.data, 'info', 'Payload', required=False, default=[])
        warnings = self.retrieve(self.data, 'warnings', 'Payload', required=False, default=[])
        errors = self.retrieve(self.data, 'errors', 'Payload', required=False, default=[])

        # Execute
        return ClientConverterCallback(identifier, success, info, warnings, errors).process_converter_callback()
