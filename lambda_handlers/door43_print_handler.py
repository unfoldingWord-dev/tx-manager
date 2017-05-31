from __future__ import unicode_literals, print_function
from door43_tools.project_printer import ProjectPrinter
from lambda_handlers.handler import Handler


class Door43PrintHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Get all params, both POST and GET and JSON from the request event
        data = {}
        if 'data' in event and isinstance(event['data'], dict):
            data = event['data']
        if 'body-json' in event and isinstance(event['body-json'], dict):
            data.update(event['body-json'])
        # Get the project ID
        project_id = self.retrieve(data, 'id', 'Parameters')
        # Set required env_vars
        env_vars = {
            'cdn_bucket': self.retrieve(event['vars'], 'cdn_bucket', 'Environment Vars'),
        }
        return ProjectPrinter(**env_vars).print_project(project_id)
