from __future__ import unicode_literals, print_function
import json
from libraries.general_tools.data_utils import json_serial
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler


class ListJobsHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        jobs = TxManager().list_jobs(self.data)
        ret = []
        if jobs:
            for job in jobs:
                ret.append(dict(job))
        return ret
