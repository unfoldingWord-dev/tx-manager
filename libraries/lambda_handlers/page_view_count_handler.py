from __future__ import unicode_literals, print_function
import json
import urllib
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.lambda_handlers.handler import Handler


class PageViewCountHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        increment = int(self.retrieve(self.data, 'increment', 'Payload', required=False, default=0))
        path = self.retrieve(self.data, 'path', 'Payload', required=False, default='')
        callback = self.retrieve(self.data, 'callback', 'Payload', required=False)

        # Execute
        data = PageMetrics().get_view_count(path, increment)
        if callback:
            return callback + '(' + json.dumps(data) + ')'
        else:
            return data
