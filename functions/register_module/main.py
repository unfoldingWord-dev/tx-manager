from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.register_module_handler import RegisterModuleHandler


def handle(event, context):
    """
    Called by a module when it is deployed to register it
    :param dict event:
    :param context:
    :return dict:
    """
    return RegisterModuleHandler().handle(event, context)
