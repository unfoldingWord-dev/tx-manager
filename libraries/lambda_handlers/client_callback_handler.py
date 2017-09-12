from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler
from libraries.client.client_callback import ClientCallback


class ClientCallbackHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        job_data = self.retrieve(event, 'data', 'payload')

        # Execute
        return ClientCallback(job_data).process_callback()
