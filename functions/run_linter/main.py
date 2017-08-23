from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.run_linter_handler import RunLinterHandler


def handle(event, context):
    """
    Called by the webhook client to request a job
    :param dict event:
    :param context:
    :return dict:
    """
    return RunLinterHandler().handle(event, context)
