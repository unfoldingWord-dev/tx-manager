import mock
import unittest
import json
import tempfile

import aws_tools.dynamodb_handler
import aws_tools.lambda_handler
import aws_tools.s3_handler


class DynamoDBHandlerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with mock.patch("aws_tools.dynamodb_handler.boto3", mock.MagicMock()):
            cls.handler = aws_tools.dynamodb_handler.DynamoDBHandler("table_name")
        cls.handler.table = mock.MagicMock()

    def setUp(self):
        self.handler.table.reset_mock()


    def test_get_item(self):
        """
        Test a successful invocation of `get_item`
        """
        expected = dict(field1="1", field2="2")
        self.handler.table.get_item.return_value = {
            "Item" : expected
        }
        self.assertEqual(self.handler.get_item("key"), expected)

    def test_get_item_malformed(self):
        """
        Test an unsuccessful invocation of `get_item`
        """
        self.handler.table.get_item.return_value = {
            "TheWrongKey": dict(field1="1", field2="2")
        }
        self.assertIsNone(self.handler.get_item("key"))

    def test_insert_item(self):
        """
        Test a successful invocation of `insert_item`
        """
        data = dict(x="x", y="y", three=3)
        self.handler.insert_item(data)
        self.handler.table.put_item.assert_called_once_with(Item=data)

    def test_update_item(self):
        """
        Test a successful invocation of `update_item`
        """
        key = {"id": 1}
        data = {"age": 40, "name": "John Doe"}
        self.handler.update_item(key, data)
        self.handler.table.update_item.assert_called_once()
        _, kwargs = self.handler.table.update_item.call_args

        self.assertIn("Key", kwargs)
        self.assertEqual(kwargs["Key"], key)

        self.assertIn("UpdateExpression", kwargs)
        # ignore whitespace and order of assignments
        expr = kwargs["UpdateExpression"].replace(" ", "")
        self.assertTrue(expr.startswith("SET"))
        self.assertIn("age=:age", expr)
        self.assertIn("#item_name=:name", expr)

        self.assertIn("ExpressionAttributeValues", kwargs)
        self.assertEqual(kwargs["ExpressionAttributeValues"],
                         {":age": 40, ":name": "John Doe"})

        self.assertIn("ExpressionAttributeNames", kwargs)
        self.assertEqual(kwargs["ExpressionAttributeNames"],
                         {"#item_name": "name"})

    def test_delete_item(self):
        """
        Test a successful invocation of `delete_item`
        """
        key = {"id": 1234}
        self.handler.delete_item(key)
        self.handler.table.delete_item.assert_called_once_with(Key=key)

    def test_query_item(self):
        """
        Test a successful invocation of `query_item`
        """
        for cond in ("ne", "lt", "lte", "gt", "gte",
                     "begins_with", "is_in", "contains"):
            self.handler.table.reset_mock()
            query = {
                "age": {
                    "condition": "eq",
                    "value": 25
                },
                "full_name": {
                    "condition": cond,
                    "value": "John Doe"
                }
            }
            data = {"age": 30, "full_name": "John Doe"}
            self.handler.table.scan.return_value = {"Items": data}
            self.assertEqual(self.handler.query_items(query), data)
            self.handler.table.scan.assert_called_once()

    def test_query_item_no_query(self):
        """
        Test a invocation of `query_item` with no query
        """
        data = {"age": 30, "full_name": "John Doe"}
        self.handler.table.scan.return_value = {"Items": data}
        self.assertEqual(self.handler.query_items(), data)
        self.handler.table.scan.assert_called_once_with()


class LambdaHandlerTest(unittest.TestCase):

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
