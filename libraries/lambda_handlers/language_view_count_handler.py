from __future__ import unicode_literals, print_function
import json
import urllib
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.lambda_handlers.handler import Handler


class LanguageViewCountHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return jsonp:
        """
        # Gather required arguments
        increment = 0
        path = ''
        callback = ''
        try:
            querystring = event['api-gateway']['params']['querystring']
            if 'callback' in querystring:
                callback = querystring['callback']
            path = urllib.unquote(querystring['path'])
            if 'increment' in querystring:
                increment = int(querystring['increment'])
        except:
            pass

        # Execute
        data = PageMetrics().get_language_view_count(path, increment)
        return callback + '(' + json.dumps(data) + ')'
