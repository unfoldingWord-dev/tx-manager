from __future__ import absolute_import, unicode_literals, print_function
import unittest
from moto import mock_dynamodb2
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler


@mock_dynamodb2
class DynamoDBHandlerTests(unittest.TestCase):
    MOCK_TABLE_NAME = 'employees'

    def setUp(self):
        self.db_handler = DynamoDBHandler(self.MOCK_TABLE_NAME)
        self.init_table()
        self.items = {}
        self.init_items()
        self.populate_table()

    def init_table(self):
        try:
            self.db_handler.table.delete()
        except:
            pass
        self.db_handler.resource.create_table(
            TableName=self.MOCK_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'full_name',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'sex',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'age',
                    'AttributeType': 'N'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )

    def init_items(self):
        self.items = {
            '121': {
                'id': '121',
                'full_name': 'John Smith',
                'sex': 'M',
                'age': 39
            },
            '122': {
                'id': '122',
                'full_name': 'Sally Jones',
                'sex': 'F',
                'age': 23
            },
            '123': {
                'id': '123',
                'full_name': 'Harriet Lott',
                'sex': 'F',
                'age': 43
            }
        }

    def populate_table(self):
        for idx in self.items:
            self.db_handler.insert_item(self.items[idx])

    def test_get_item(self):
        """Test a successful invocation of `get_item`."""
        item = self.db_handler.get_item({'id': '123'})
        expected = self.items['123']
        self.assertItemsEqual(item, expected)

    def test_get_item_malformed(self):
        """Test an unsuccessful invocation of `get_item`."""
        self.assertIsNone(self.db_handler.get_item({'id': 'doesnotexist'}))

    def test_insert_item(self):
        """Test a successful invocation of `insert_item`."""
        data = {
            'id': '555',
            'full_time': 'Richard Nixon',
            'sex': 'M',
            'age': 90
        }
        self.db_handler.insert_item(data)
        self.assertItemsEqual(self.db_handler.get_item({'id': data['id']}), data)

    def test_update_item(self):
        """Test a successful invocation of `update_item`."""
        key = {"id": "121"}
        data = {"age": 40, "full_name": "John Doe"}
        self.db_handler.update_item(key, data)
        item = self.db_handler.get_item({'id': key['id']})
        self.assertEqual(item['age'], data['age'])
        self.assertEqual(item['full_name'], data['full_name'])

    def test_delete_item(self):
        """Test a successful invocation of `delete_item`."""
        key = {"id": '123'}
        self.db_handler.delete_item(key)
        self.assertIsNone(self.db_handler.get_item(key))
        self.assertEqual(self.db_handler.get_item_count(), len(self.items)-1)

    def test_scan_items(self):
        """ Test a successful invocation of `scan_items`."""
        # Note: Moto currently doesn't support FilterExpression, See: https://github.com/spulec/moto/issues/715
        for cond in ('ne', 'lt', 'lte', 'gt', 'gte'):
            query = {
                'age': {
                    'condition': cond,
                    'value': 39
                },
            }
            items = self.db_handler.scan_items(query)
            self.assertEqual(len(items), len(self.items))
            for item in items:
                self.assertItemsEqual(item, self.items[item['id']])
        for cond in ('begins_with', 'is_in', 'contains'):
            query = {
                'full_name': {
                    'condition': cond,
                    'value': 'John'
                },
            }
            items = self.db_handler.scan_items(query)
            self.assertEqual(len(items), len(self.items))
            for item in items:
                self.assertItemsEqual(item, self.items[item['id']])

    def test_scan_items_no_query(self):
        """Test a invocation of `scan_items` with no query."""
        self.assertEqual(len(self.db_handler.scan_items()), len(self.items))
