from __future__ import print_function
from logging import Logger
from manager.manager import TxManager
from aws_tools.dynamodb_handler import DynamoDBHandler


class RegisterModuleHandler(object):

    @staticmethod
    def handle_register_module(event, context, dynamodb_handler, logger):
        """
        :param dict event:
        :param context:
        :param DynamoDBHandler dynamodb_handler:
        :param Logger logger:
        :return:
        """
        try:
            # Get all params, both POST and GET and JSON from the request event
            module = {}
            if 'data' in event and isinstance(event['data'], dict):
                module = event['data']
            if 'body-json' in event and event['body-json'] and isinstance(event['body-json'], dict):
                module.update(event['body-json'])
            env_vars = {}
            if 'vars' in event and isinstance(event['vars'], dict):
                env_vars = event['vars']
            env_vars['dynamodb_handler'] = DynamoDBHandler
            env_vars['logger'] = logger
            return TxManager(**env_vars).register_module(module)
        except Exception as e:
            raise Exception('Bad request: {0}'.format(e.message))
