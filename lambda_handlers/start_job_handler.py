from __future__ import unicode_literals, print_function
from manager.manager import TxManager
from lambda_handlers.handler import Handler


class StartJobHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        """
        for record in event['Records']:
            if record['eventName'] == 'INSERT' and 'job_id' in record['dynamodb']['Keys']:
                job_id = record['dynamodb']['Keys']['job_id']['S']
                TxManager().start_job(job_id)
