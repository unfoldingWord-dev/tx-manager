from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.search_projects_handler import SearchProjectsHandler


def handle(event, context):
    """
    Called by API Gateway to search projects and return a JSON array
    :param dict event:
    :param context:
    :return dict:
    """
    return SearchProjectsHandler().handle(event, context)
