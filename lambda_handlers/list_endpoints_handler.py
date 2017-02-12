from __future__ import unicode_literals, print_function
from manager.manager import TxManager
from lambda_handlers.handler import Handler


class ListEndpointsHandler(Handler):

    def __handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        vars = {}
        if 'vars' in event and isinstance(event['vars'], dict):
            vars = event['vars']
        vars['dynamodb_handler_class'] = self.dynamodb_handler_class
        vars['logger'] = self.logger
        return TxManager(**vars).list_endpoints()

