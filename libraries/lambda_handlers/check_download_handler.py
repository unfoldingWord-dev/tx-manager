from __future__ import unicode_literals, print_function
import json
from libraries.door43_tools.download_metrics import DownloadMetrics
from libraries.lambda_handlers.handler import Handler


class CheckDownloadHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return jsonp:
        """

        # Set required env_vars
        env_vars = {
            'pre_convert_bucket': self.retrieve(event['vars'], 'pre_convert_bucket', 'Environment Vars'),
        }

        commit_id = ''
        callback = ''
        try:
            querystring = event['api-gateway']['params']['querystring']
            commit_id = querystring['commit_id']
            if 'callback' in querystring:
                callback = querystring['callback']

        except:
            pass

        data = DownloadMetrics(**env_vars).check_download(commit_id)
        return callback + '(' + json.dumps(data) + ')'
