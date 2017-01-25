from __future__ import unicode_literals, print_function
from logging import Logger
from manager.manager import TxManager
from aws_tools.dynamodb_handler import DynamoDBHandler


class StartJobHandler(object):

    @staticmethod
    def handle_start_job(event, context, dynamodb_handler, logger):
        """
        :param dict event:
        :param context:
        :param DynamoDBHandler dynamodb_handler:
        :param Logger logger:
        :return:
        """
        print("------------PROCESSING DB STREAM---------------------")
        for record in event['Records']:
            try:
                if record['eventName'] == 'INSERT' and 'job_id' in record['dynamodb']['Keys']:
                    job_id = record['dynamodb']['Keys']['job_id']['S']
                    TxManager(dynamodb_handler=dynamodb_handler, logger=logger).start_job(job_id)
            except Exception as e:
                print("Failed for record:")
                print(record)
                print("Error:")
                print(e)
        print("------------END PROCESSING DB STREAM---------------------")

