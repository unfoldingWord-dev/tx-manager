from __future__ import unicode_literals, print_function
import json
import urllib
from libraries.lambda_handlers.handler import Handler
from libraries.manifest.view_count import ViewCount


class ViewCountHandler(Handler):

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
        # Set required env_vars
        env_vars = {
            'manifest_table_name': self.retrieve(event['vars'], 'manifest_table_name', 'Environment Vars')
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

        data = ViewCount(**env_vars).get_view_count(path, increment)
        return callback + '(' + json.dumps(data) + ')'
