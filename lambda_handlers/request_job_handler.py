from __future__ import unicode_literals, print_function
from manager.manager import TxManager
from lambda_handlers.handler import Handler


class RequestJobHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Get all params, both POST and GET and JSON from the request event
        data = {}
        if 'data' in event and isinstance(event['data'], dict):
            data = event['data']
        if 'body-json' in event and event['body-json'] and isinstance(event['body-json'], dict):
            data.update(event['body-json'])
        # Set required env_vars
        env_vars = {
            'api_url': self.retrieve(event['vars'], 'api_url', 'Environment Vars'),
            'gogs_url': self.retrieve(event['vars'], 'gogs_url', 'Environment Vars'),
            'cdn_url': self.retrieve(event['vars'], 'cdn_url', 'Environment Vars'),
            'job_table_name': self.retrieve(event['vars'], 'job_table_name', 'Environment Vars'),
            'module_table_name': self.retrieve(event['vars'], 'module_table_name', 'Environment Vars'),
            'cdn_bucket': self.retrieve(event['vars'], 'cdn_bucket', 'Environment Vars')
        }
        return TxManager(**env_vars).setup_job(data)
