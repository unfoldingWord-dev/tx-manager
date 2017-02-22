from __future__ import unicode_literals, print_function
from manager.manager import TxManager
from lambda_handlers.handler import Handler


class RequestJobHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Get all params, both POST and GET and JSON from the request event
        job = {}
        if 'data' in event and isinstance(event['data'], dict):
            job = event['data']
        if 'body-json' in event and event['body-json'] and isinstance(event['body-json'], dict):
            job.update(event['body-json'])
        vars = {}
        if 'vars' in event and isinstance(event['vars'], dict):
            vars = event['vars']
        if 'source' in job and 'job_id' not in job:
            # if 'source' is given, and no job_id, that means to setup a new job for conversion
            job['job_id'] = context.aws_request_id
            return TxManager(**vars).setup_job(job)
        else:
            # Else we just list all jobs based on the given query data
            return TxManager(**vars).list_jobs(job)
