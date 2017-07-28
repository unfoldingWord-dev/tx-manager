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
        # Set required env_vars
        env_vars = {
            'language_stats_table_name': self.retrieve(event['vars'], 'language_stats_table_name', 'Environment Vars')
        }

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

        data = PageMetrics(**env_vars).get_language_view_count(path, increment)
        return callback + '(' + json.dumps(data) + ')'
