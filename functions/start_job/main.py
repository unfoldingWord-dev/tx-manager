from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.start_job_handler import StartJobHandler


def handle(event, context):
    """
    Triggered by adding a file to the cdn.door43.org/temp S3 folder
    :param dict event:
    :param context:
    :return dict:
    """
    return StartJobHandler().handle(event, context)
