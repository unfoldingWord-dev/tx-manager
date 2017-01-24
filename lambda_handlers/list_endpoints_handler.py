from __future__ import unicode_literals, print_function
from logging import Logger
from manager.manager import TxManager
from aws_tools.dynamodb_handler import DynamoDBHandler


class ListEndpointsHandler(object):

    @staticmethod
    def handle_list_endpoints(event, context, dynamodb_handler, logger):
        """
        :param dict event:
        :param context:
        :param DynamoDBHandler dynamodb_handler:
        :param Logger logger:
        :return:
        """
        try:
            env_vars = {}
            if 'vars' in event and isinstance(event['vars'], dict):
                env_vars = event['vars']
            env_vars['dynamodb_handler'] = DynamoDBHandler
            env_vars['logger'] = logger
            return TxManager(**env_vars).list_endpoints()
        except Exception as e:
            raise Exception('Bad request: {0}'.format(e))
