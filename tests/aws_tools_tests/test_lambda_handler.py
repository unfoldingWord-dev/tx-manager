from __future__ import unicode_literals
import mock
import unittest
import json
import aws_tools.lambda_handler


class LambdaHandlerTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with mock.patch("aws_tools.lambda_handler.boto3", mock.MagicMock()):
            cls.handler = aws_tools.lambda_handler.LambdaHandler()
        cls.handler.client = mock.MagicMock()

    def setUp(self):
        self.handler.client.reset_mock()

    def test_invoke(self):
        """
        Test a successful call of `invoke`
        """
        payload = {"arg1": "value1", "arg2": "value2"}
        response = {"StatusCode": 123, "LogResult": "log"}
        self.handler.client.invoke.return_value = response
        self.assertEqual(self.handler.invoke("function_name", payload), response)
        self.handler.client.invoke.assert_called_once_with(
            FunctionName="function_name",
            Payload=json.dumps(payload)
        )
