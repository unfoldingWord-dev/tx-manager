from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.lint_handler import LintHandler
from libraries.linters.ulb_linter import UlbLinter


def handle(event, context):
    """
    Invoked by webhook client to run the linter
    :param dict event:
    :param context:
    :return dict:
    """
    return LintHandler(UlbLinter).handle(event, context)
