from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.client_converter_callback_handler import ClientConverterCallbackHandler


def handle(event, context):
    """
    Called by API Gateway when the converter has finished and calls the client converter callback
    :param dict event:
    :param context:
    :return dict:
    """
    return ClientConverterCallbackHandler().handle(event, context)
