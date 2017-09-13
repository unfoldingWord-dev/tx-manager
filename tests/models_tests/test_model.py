from __future__ import absolute_import, unicode_literals, print_function
import unittest
from moto import mock_dynamodb2
from libraries.models.module import Model
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler


class MyModel(Model):
    db_keys = [
        'field1'
    ]

    db_fields = [
        'field1',
        'field2'
    ]

    def __init__(self, *args, **kwargs):
        self.field1 = None
        self.field2 = None
        kwargs['db_handler'] = DynamoDBHandler(ModelTests.TABLE_NAME)
        super(MyModel, self).__init__(*args, **kwargs)


@mock_dynamodb2
class ModelTests(unittest.TestCase):
    TABLE_NAME = 'my-module-table'

    def setUp(self):
        """Runs before each test."""
        self.db_handler = DynamoDBHandler(ModelTests.TABLE_NAME)
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
            TableName=ModelTests.TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'field1',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'field1',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )

    def init_items(self):
        self.items = {
            'mymodel1': {
                'field1': 'mymodel1',
                'field2': 'something',
            },
            'mymodel2': {
                'field1': 'mymodel2',
                'field2': 'something else',
            },
        }

    def populate_table(self):
        for idx in self.items:
            MyModel().insert(self.items[idx])

    def test_populate(self):
        """Test populate method."""
        obj = MyModel()
        data = {
            'field1': 'value1',
            'field2': 'value2',
            'field3': 'value3'
        }
        obj.populate(data)
        self.assertTrue(hasattr(obj, 'field1'))
        self.assertEqual(obj.field2, 'value2')
        self.assertFalse(hasattr(obj, 'field3'))
        
    def test_query(self):
        models = MyModel().query()
        self.assertEqual(len(models), len(self.items))
        for model in models:
            self.assertEqual(model.get_db_data(), MyModel(self.items[model.field1]).get_db_data())

    def test_load(self):
        model = MyModel().load({'field1': 'mymodel2'})
        self.assertEqual(model.get_db_data(), MyModel(self.items['mymodel2']).get_db_data())

    def test_insert(self):
        # Insert by giving fields in the constructor
        MyModel({'field1': 'mymodel3', 'field2': 'something good'}).insert()
        model = MyModel().load({'field1': 'mymodel3'})
        self.assertEqual(model.field2, 'something good')
        # Insert by giving data to the insert() method
        MyModel().insert({'field1': 'mymodel4', 'field2': 'something better'})
        model = MyModel().load({'field1': 'mymodel4'})
        self.assertEqual(model.field2, 'something better')

    def test_update(self):
        model = MyModel().load({'field1': 'mymodel1'})

        # Update by setting fields and calling update()
        model.field2 = 'change'
        model.update()
        model = MyModel().load({'field1': 'mymodel1'})
        self.assertEqual(model.field2, 'change')

        # Update by giving a dict to update()
        model.update({'field1': 'cannot change', 'field2': 'can change'})
        self.assertEqual(model.field1, 'mymodel1')  # didn't change
        model = MyModel().load({'field1': 'mymodel1'})
        self.assertEqual(model.field2, 'can change')

    def test_delete_model(self):
        MyModel('model2').delete()
        model = MyModel('model2')
        self.assertIsNone(model.field1)

    def test_count(self):
        self.assertEqual(MyModel().count(), len(self.items))


if __name__ == "__main__":
    unittest.main()
