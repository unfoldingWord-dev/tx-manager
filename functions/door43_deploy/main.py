from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.door43_deploy_handler import Door43DeployHandler


def handle(event, context):
    """
    Triggered by adding a project's revision directory to the u/ directory of the cdn.door43.org bucket
    :param dict event:
    :param context:
    :return dict:
    """
    return Door43DeployHandler().handle(event, context)
