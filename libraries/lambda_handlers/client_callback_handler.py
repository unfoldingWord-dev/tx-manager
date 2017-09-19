from __future__ import unicode_literals, print_function
import json
from libraries.general_tools.data_utils import json_serial
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
        return json.dumps(ClientCallback(job_data).process_callback(), default=json_serial)
