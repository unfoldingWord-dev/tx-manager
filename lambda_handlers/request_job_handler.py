from __future__ import unicode_literals, print_function
from logging import Logger
from manager.manager import TxManager
from aws_tools.dynamodb_handler import DynamoDBHandler


class RequestJobHandler(object):

    @staticmethod
    def handle_request_job(event, context, dynamodb_handler, logger):
        """
        :param dict event:
        :param context:
        :param DynamoDBHandler dynamodb_handler:
        :param Logger logger:
        :return:
        """
        try:
            # Get all params, both POST and GET and JSON from the request event
            job = {}
            if 'data' in event and isinstance(event['data'], dict):
                job = event['data']
            if 'body-json' in event and event['body-json'] and isinstance(event['body-json'], dict):
                job.update(event['body-json'])

            env_vars = {}
            if 'vars' in event and isinstance(event['vars'], dict):
                env_vars = event['vars']
            env_vars['dynamodb_handler'] = DynamoDBHandler
            env_vars['logger'] = logger
            # if 'source' is given, and no job_id, that means to setup a new job for conversion
            if 'source' in job and 'job_id' not in job:
                job['job_id'] = context.aws_request_id
                return TxManager(**env_vars).setup_job(job)
            # Else we just list all jobs based on the given query data
            else:
                return TxManager(env_vars, dynamodb_handler, logger).list_jobs(job)
        except Exception as e:
            raise Exception('Bad Request: {0}'.format(e))


