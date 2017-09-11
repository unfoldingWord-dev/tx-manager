from __future__ import unicode_literals, print_function

from libraries.lambda_handlers.check_download_handler import CheckDownloadHandler


def handle(event, context):
    """
    Called by API Gateway to check if a download file exists
    :param dict event:
    :param context:
    :return dict:
    """
    return CheckDownloadHandler().handle(event, context)
