from __future__ import unicode_literals, print_function
import json
from libraries.door43_tools.project_search import ProjectSearch
from libraries.lambda_handlers.handler import Handler


class SearchProjectsHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        callback = self.retrieve(self.data, 'callback', required=False)

        # Execute
        results = ProjectSearch().search_projects(self.data)
        if callback:
            return '{0}({1})'.format(callback, json.dumps(results))
        else:
            return results
