from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.language_view_count_handler import LanguageViewCountHandler


def handle(event, context):
    """
    Called by API Gateway to get the view count of a language page
    :param dict event:
    :param context:
    :return dict:
    """
    return LanguageViewCountHandler().handle(event, context)
