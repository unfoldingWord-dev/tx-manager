from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.dashboard_handler import DashboardHandler


def handle(event, context):
    """
    Called by API Gateway when user wants a list of endpoints
    :param dict event:
    :param context:
    :return dict:
    """
    return DashboardHandler().handle(event, context)
