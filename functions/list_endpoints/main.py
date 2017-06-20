from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.list_endpoints_handler import ListEndpointsHandler


def handle(event, context):
    """
    Called by API Gateway when user wants a list of endpoints
    :param dict event:
    :param context:
    :return dict:
    """
    return ListEndpointsHandler().handle(event, context)
