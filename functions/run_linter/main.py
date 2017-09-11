from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.run_linter_handler import RunLinterHandler


def handle(event, context):
    """
    Invoked by webhook client to run the linter
    :param dict event:
    :param context:
    :return dict:
    """
    return RunLinterHandler().handle(event, context)
