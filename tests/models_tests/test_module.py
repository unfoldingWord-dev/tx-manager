from __future__ import absolute_import, unicode_literals, print_function
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.models.module import TxModule
from libraries.app.app import App


@mock_dynamodb2
class TxModuleTests(TestCase):

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        self.init_table()
        self.items = {}
        self.init_items()
        self.populate_table()

    def init_table(self):
        try:
            App.module_db_handler().table.delete()
        except:
            pass

        App.module_db_handler().resource.create_table(
            TableName=App.module_table_name,
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
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
            'module1': {
                'name': 'module1',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['obs', 'ulb'],
                'input_format': 'md',
                'output_format': 'html',
                'public_links': ['http://api.exmaple.com/tx/convert/md2html'],
                'private_links': ['http://api.example.com/tx/private/module1'],
                'options': {'pageSize': 'A4'}
            },
            'module2': {
                'name': 'module2',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['ulb'],
                'input_format': 'usfm',
                'output_format': 'html',
                'public_links': ['http://api.example.com/tx/convert/usfm2html'],
                'private_links': [],
                'options': {'pageSize': 'A4'}
            },
            'module3': {
                'name': 'module3',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['other', 'yet_another'],
                'input_format': 'md',
                'output_format': 'html',
                'public_links': [],
                'private_links': [],
                'options': {}
            },
        }

    def populate_table(self):
        for idx in self.items:
            App.module_db_handler().insert_item(self.items[idx])

    def test_query_module(self):
        tx_modules = TxModule().query()
        self.assertEqual(len(tx_modules), len(self.items))
        for tx_module in tx_modules:
            self.assertEqual(tx_module.get_db_data(), TxModule(self.items[tx_module.name]).get_db_data())

    def test_load_module(self):
        # Test loading by just giving it the name in the constructor
        tx_module = TxModule('module1')
        self.assertEqual(tx_module.get_db_data(), TxModule(self.items['module1']).get_db_data())
        # Test loading by just giving it only the name in the data array in the constructor
        tx_module = TxModule({'name': 'module2'})
        self.assertEqual(tx_module.get_db_data(), TxModule(self.items['module2']).get_db_data())

    def test_update_module(self):
        tx_module = TxModule()
        tx_module.repo_name = self.items['module3']['name']
        tx_module.load()
        tx_module.output_format = 'usfm'
        tx_module.update()
        tx_module.load()
        self.assertEqual(tx_module.output_format, 'usfm')

    def test_delete_module(self):
        tx_module = TxModule()
        tx_module.name = self.items['module1']['name']
        tx_module.load()
        self.assertIsNotNone(tx_module.name)
        tx_module.delete()
        tx_module.load()
        self.assertIsNone(tx_module.name)
