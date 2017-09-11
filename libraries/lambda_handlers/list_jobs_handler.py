from __future__ import unicode_literals, print_function
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler


class ListJobsHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        return TxManager(**env_vars).list_jobs(self.data)
