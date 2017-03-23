from __future__ import unicode_literals, print_function
from manager.manager import TxManager
from lambda_handlers.handler import Handler


class DashboardHandler(Handler):

    def __handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        vars = {}
        if 'vars' in event and isinstance(event['vars'], dict):
            vars = event['vars']
        return TxManager(**vars).generate_dashboard()
