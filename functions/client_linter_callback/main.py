from __future__ import unicode_literals, print_function

from libraries.lambda_handlers.client_linter_callback_handler import ClientLinterCallbackHandler


def handle(event, context):
    """
    Invoked by webhook client to run the linter
    :param dict event:
    :param context:
    :return dict:
    """
    return ClientLinterCallbackHandler().handle(event, context)
