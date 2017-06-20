from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.request_job_handler import RequestJobHandler


def handle(event, context):
    """
    Called by the webhook client to request a job
    :param dict event:
    :param context:
    :return dict:
    """
    return RequestJobHandler().handle(event, context)
