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
        data = {}
        if 'data' in event and isinstance(event['data'], dict):
            data = event['data']
        if 'body-json' in event and isinstance(event['body-json'], dict):
            data.update(event['body-json'])
        callback = self.retrieve(data, 'callback', required=False, default='')
        results = ProjectSearch().search_projects(data)
        return callback + '(' + json.dumps(results) + ')'
