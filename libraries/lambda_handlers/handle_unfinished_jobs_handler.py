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
            'api_url': self.retrieve(event['vars'], 'api_url', 'Environment Vars'),
            'gogs_url': self.retrieve(event['vars'], 'gogs_url', 'Environment Vars'),
            'cdn_url': self.retrieve(event['vars'], 'cdn_url', 'Environment Vars'),
            'job_table_name': self.retrieve(event['vars'], 'job_table_name', 'Environment Vars'),
            'module_table_name': self.retrieve(event['vars'], 'module_table_name', 'Environment Vars')
        }
        return TxManager(**env_vars).handle_unfinished_jobs()
