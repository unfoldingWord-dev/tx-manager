from __future__ import unicode_literals, print_function
from libraries.manager.manager import TxManager
from libraries.lambda_handlers.handler import Handler
from libraries.app.app import App


class StartJobHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        """
        for record in event['Records']:
            if record['eventName'] == 'INSERT' and 'job_id' in record['dynamodb']['Keys']:
                # Get the job table name
                ddbARN = record['eventSourceARN']
                ddbTable = ddbARN.split(':')[5].split('/')[1]
                job_table_name = ddbTable
                # Get the prefix of the job table name and add it to tx-module
                prefix = job_table_name[:-(len('tx-job'))]
                App(prefix=prefix)
                job_id = record['dynamodb']['Keys']['job_id']['S']
                TxManager().start_job(job_id)
