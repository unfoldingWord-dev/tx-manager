from __future__ import unicode_literals, print_function
import json
from libraries.general_tools.data_utils import json_serial
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler


class StartJobHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        """
        job_id = self.retrieve(self.data, 'job_id', 'Payload')
        return json.dumps(TxManager().start_job(job_id), default=json_serial)
