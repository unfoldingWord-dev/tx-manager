from __future__ import unicode_literals, print_function
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler
from libraries.app.app import App


class StartJobHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        """
        job_id = self.retrieve(self.data, 'job_id', 'Payload')
        return TxManager().start_job(job_id)
