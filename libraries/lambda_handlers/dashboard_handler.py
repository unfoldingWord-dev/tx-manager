from __future__ import unicode_literals, print_function
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler


class DashboardHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        try:
            querystring = event['api-gateway']['params']['querystring']
            max_failures = int(querystring['failures'])
        except:
            max_failures = TxManager.MAX_FAILURES

        return TxManager().generate_dashboard(max_failures)
