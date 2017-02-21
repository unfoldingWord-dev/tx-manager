from __future__ import print_function
from manager.manager import TxManager
from lambda_handlers.handler import Handler


class RegisterModuleHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Get all params, both POST and GET and JSON from the request event
        module = {}
        if 'data' in event and isinstance(event['data'], dict):
            module = event['data']
        if 'body-json' in event and event['body-json'] and isinstance(event['body-json'], dict):
            module.update(event['body-json'])
        vars = {}
        if 'vars' in event and isinstance(event['vars'], dict):
            vars = event['vars']
        vars['api_id'] = context.api
        return TxManager(**vars).register_module(module)
