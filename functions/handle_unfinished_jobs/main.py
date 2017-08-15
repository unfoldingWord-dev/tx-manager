from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handle_unfinished_jobs_handler import UnfinishedJobsHandler


def handle(event, context):
    """
    Triggered by an AWS event every 5 minutes
    :param dict event:
    :param context:
    :return dict:
    """
    return UnfinishedJobsHandler().handle(event, context)
