from __future__ import unicode_literals, print_function
from manager.manager import TxManager
from lambda_handlers.handler import Handler


class ListEndpointsHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        env_vars = {}
        if 'vars' in event and isinstance(event['vars'], dict):
            env_vars = event['vars']
        return TxManager(**env_vars).list_endpoints()

