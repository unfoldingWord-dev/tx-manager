from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.client_webhook_handler import ClientWebhookHandler


def handle(event, context):
    """
    Called by API Gateway when a Gogs repo triggers a webhook with API Gateway URL
    :param dict event:
    :param context:
    :return dict:
    """
    return ClientWebhookHandler().handle(event, context)
