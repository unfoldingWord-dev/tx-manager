from __future__ import unicode_literals, print_function
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler


class UnfinishedJobsHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return list:
        """
        # Set required env_vars
        env_vars = {
            'cdn_url': self.retrieve(event, 'cdn_url', 'event'),
            'job_table_name': self.retrieve(event, 'job_table_name', 'event'),
        }
        return TxManager(**env_vars).handle_unfinished_jobs()
