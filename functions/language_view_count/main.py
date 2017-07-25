from __future__ import unicode_literals, print_function

from libraries.lambda_handlers.language_view_count_handler import LanguageViewCountHandler


def handle(event, context):
    """
    Called by API Gateway when user wants a list of endpoints
    :param dict event:
    :param context:
    :return dict:
    """
    return LanguageViewCountHandler().handle(event, context)
