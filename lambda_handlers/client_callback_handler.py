from __future__ import unicode_literals, print_function
from lambda_handlers.handler import Handler
from client.client_callback import ClientCallback


class ClientCallbackHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        job = self.retrieve(event, 'data', 'payload')
        vars = self.retrieve(event, 'vars', 'payload')
        # Check vars exist
        self.retrieve(vars, 'gogs_url', 'payload')
        self.retrieve(vars, 'cdn_bucket', 'payload')
        self.retrieve(job, 'identifier', 'job')
        return ClientCallback(**vars).process_callback()
