from __future__ import unicode_literals, print_function
from libraries.door43_tools.project_printer import ProjectPrinter
from libraries.lambda_handlers.handler import Handler


class Door43PrintHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather required arguments
        project_id = self.retrieve(self.data, 'id', 'Parameters')

        # Execute
        return ProjectPrinter.print_project(project_id)
