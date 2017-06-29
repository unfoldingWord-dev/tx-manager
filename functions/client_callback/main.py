from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.client_callback_handler import ClientCallbackHandler


def handle(event, context):
    """
    Called by API Gateway when the tx-manager is notified of a finished or failed conversion
    :param dict event:
    :param context:
    :return dict:
    """
    return ClientCallbackHandler().handle(event, context)
