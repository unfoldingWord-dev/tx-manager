from __future__ import absolute_import, unicode_literals, print_function
import os
from datetime import datetime
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.manager.manager import TxManager
from libraries.general_tools.file_utils import load_yaml_object


@mock_dynamodb2
class ManifestTests(TestCase):
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        self.manager = TxManager()
        self.handler = self.manager.manifest_db_handler
        self.table = None
        self.items = []
        self.init_table()
        self.init_items()
        self.populate_table()

    def init_table(self):
        self.table = self.handler.resource.create_table(
            TableName=TxManager.MANIFEST_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'repo_name',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'user_name',
                    'KeyType': 'RANGE'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'repo_name',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_name',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

    def init_items(self):
        self.items = [{
                'repo_name': 'en_obs',
                'user_name': 'Door43',
                'lang_code': 'en',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 2,
                'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'manifest': load_yaml_object(os.path.join(self.resources_dir, 'obs_manifest.yaml'))
            },
            {
                'repo_name': 'en_obs',
                'user_name': 'johndoe',
                'lang_code': 'en',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 2,
                'last_updated': '2016-12-21T05:23:01Z',
                'manifest': load_yaml_object(os.path.join(self.resources_dir, 'obs_manifest.yaml'))
            },
            {
                'repo_name': 'fr_ulb',
                'user_name': 'francis',
                'lang_code': 'fr',
                'resource_id': 'ulb',
                'resource_type': 'bundle',
                'title': 'Unlocked Literal Bible',
                'views': 12,
                'last_updated': '2017-02-11T15:43:11Z',
                'manifest': load_yaml_object(os.path.join(self.resources_dir, 'obs_manifest.yaml'))
            }]

    def populate_table(self):
        for item in self.items:
            self.handler.insert_item(item)

    def test_query_manifest(self):
        self.assertEqual(self.table.name, TxManager.MANIFEST_TABLE_NAME)
        self.assertEqual(len(self.manager.query_manifests()), 3)
        manifest = self.manager.get_manifest(self.items[1]['repo_name'], self.items[1]['user_name'])
        self.assertEqual(manifest.title, self.items[1]['title'])
        self.assertEqual(manifest.manifest, self.items[1]['manifest'])

    def test_update_manifest(self):
        manifest = self.manager.get_manifest(self.items[2]['repo_name'], self.items[2]['user_name'])
        manifest.resource_id = 'udb'
        manifest.title = 'Unlocked Dynamic Bible'
        self.manager.update_manifest(manifest)
        manifest = self.manager.get_manifest(self.items[2]['repo_name'], self.items[2]['user_name'])
        self.assertEqual(manifest.resource_id, 'udb')

    def test_delete_manifest(self):
        manifest = self.manager.get_manifest(self.items[0]['repo_name'], self.items[0]['user_name'])
        self.assertIsNotNone(manifest.repo_name)
        self.manager.delete_manifest(manifest)
        manifest = self.manager.get_manifest(self.items[0]['repo_name'], self.items[0]['user_name'])
        self.assertIsNone(manifest.repo_name)
