from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler
from libraries.linters.client_linter_callback import ClientLinterCallback


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
        info = self.retrieve(self.data, 'info', 'Payload', required=False, default=[])
        warnings = self.retrieve(self.data, 'warnings', 'Payload', required=False, default=[])
        errors = self.retrieve(self.data, 'errors', 'Payload', required=False, default=[])
        s3_results_key = self.retrieve(self.data, 's3_results_key', 'Payload')

        # Execute
        return ClientLinterCallback(identifier, success, info, warnings, errors, s3_results_key).process_callback()
