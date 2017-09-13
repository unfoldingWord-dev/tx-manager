from __future__ import unicode_literals, print_function
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler


class ListEndpointsHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Execute
        return TxManager().list_endpoints()
