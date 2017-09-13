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
        # Gather arguments
        commit_id = self.retrieve(self.data, 'commit_id', 'Payload', required=False)
        callback = self.retrieve(self.data, 'callback', 'Payload', required=False)

        # Execute
        data = DownloadMetrics().check_download(commit_id)
        if callback:
            return callback + '(' + json.dumps(data) + ')'
        else:
            return data
