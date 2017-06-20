from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.list_jobs_handler import ListJobsHandler


def handle(event, context):
    """
    Called by the wbhook client to list jobs to get their status
    :param dict event:
    :param context:
    :return dict:
    """
    print("EVENT:")
    print(event)
    return ListJobsHandler().handle(event, context)
