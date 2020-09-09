from __future__ import unicode_literals, print_function
import json
import boto3


class LambdaHandler(object):
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, aws_region_name=None):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region_name = aws_region_name
        self.client = None
        self.setup_resources()

    def setup_resources(self):
        self.client = boto3.client('lambda',
                                   aws_access_key_id=self.aws_access_key_id,
                                   aws_secret_access_key=self.aws_secret_access_key,
                                   region_name=self.aws_region_name)

    def invoke(self, function_name, payload, async=False):
        invocation_type = 'RequestResponse' if not async else 'Event'
        return self.client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            LogType='Tail',
            Payload=json.dumps(payload)
        )
