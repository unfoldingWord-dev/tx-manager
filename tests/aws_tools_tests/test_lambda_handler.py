from __future__ import absolute_import, unicode_literals, print_function
import io
import json
import zipfile
from unittest import TestCase
from libraries.aws_tools.lambda_handler import LambdaHandler
from moto import mock_lambda


@mock_lambda
class LambdaHandlerTests(TestCase):
    def setUp(self):
        """Runs before each test."""
        self.handler = LambdaHandler()
        self.init_lambda("""
def lambda_handler(event, context):
    return event
        """)

    def init_lambda(self, fx):
        zip_output = io.BytesIO()
        zip_file = zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED)
        zip_file.writestr('lambda_function.zip', fx)
        zip_file.close()
        zip_output.seek(0)

        self.handler.client.create_function(
            FunctionName='testFunction',
            Runtime='python2.7',
            Role='test-iam-role',
            Handler='lambda_function.handler',
            Code={
                'ZipFile': zip_output.read()
            },
            Description='test lambda function',
            Timeout=3,
            MemorySize=128,
            Publish=True,
        )

    def test_setup_resources(self):
        my_handler = LambdaHandler(aws_access_key_id='access_key', aws_secret_access_key='secret_key',
                                   aws_region_name='us-west-1')
        self.assertEqual(my_handler.aws_access_key_id, 'access_key')
        self.assertEqual(my_handler.aws_secret_access_key, 'secret_key')
        self.assertEqual(my_handler.aws_region_name, 'us-west-1')

    def test_invoke(self):
        result = self.handler.invoke('testFunction', {'test': 123})
        self.assertEqual(result["StatusCode"], 202)
        self.assertEqual(json.loads(result['Payload'].read().decode('utf-8')), {'test': 123})
