from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.door43_print_handler import Door43PrintHandler


def handle(event, context):
    """
    Called by API Gateway when a user wants to print a whole project on live.door43.org
    :param dict event:
    :param context:
    :return dict:
    """
    return Door43PrintHandler().handle(event, context)
