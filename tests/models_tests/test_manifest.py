from __future__ import absolute_import, unicode_literals, print_function
import os
from datetime import datetime
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.general_tools.file_utils import load_yaml_object
from libraries.models.manifest import TxManifest


@mock_dynamodb2
class TxManifestTests(TestCase):
    MANIFEST_TABLE_NAME = 'test-manifest'
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    setup_table = False

    def setUp(self):
        self.db_handler = DynamoDBHandler(TxManifestTests.MANIFEST_TABLE_NAME)
        if not TxManifestTests.setup_table:
            self.init_table()
            TxManifestTests.setup_table = True
        self.items = {}
        self.init_items()
        self.populate_table()

    def init_table(self):
        self.db_handler.resource.create_table(
            TableName=TxManifestTests.MANIFEST_TABLE_NAME,
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
            },
        )

    def init_items(self):
        self.items = {
            'Door43/en_obs': {
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
            'johndoe/en_obs': {
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
            'francis/fr_ulb': {
                'repo_name': 'fr_ulb',
                'user_name': 'francis',
                'lang_code': 'fr',
                'resource_id': 'ulb',
                'resource_type': 'bundle',
                'title': 'Unlocked Literal Bible',
                'views': 12,
                'last_updated': '2017-02-11T15:43:11Z',
                'manifest': load_yaml_object(os.path.join(self.resources_dir, 'obs_manifest.yaml'))
            },
        }

    def populate_table(self):
        for idx in self.items:
            TxManifest(db_handler=self.db_handler).insert(self.items[idx])

    def test_query_manifest(self):
        manifests = TxManifest(db_handler=self.db_handler).query()
        self.assertEqual(len(manifests), len(self.items))
        for manifest in manifests:
            self.assertEqual(manifest.get_db_data(), TxManifest(self.items['{0}/{1}'.format(manifest.user_name, manifest.repo_name)]).get_db_data())

    def test_update_manifest(self):
        manifest = TxManifest(db_handler=self.db_handler)
        manifest.repo_name = self.items['francis/fr_ulb']['repo_name']
        manifest.user_name = self.items['francis/fr_ulb']['user_name']
        manifest.load()
        manifest.resource_id = 'udb'
        manifest.title = 'Unlocked Dynamic Bible'
        manifest.update()
        manifest.load()
        self.assertEqual(manifest.resource_id, 'udb')

    def test_delete_manifest(self):
        manifest = TxManifest(db_handler=self.db_handler)
        manifest.repo_name = self.items['Door43/en_obs']['repo_name']
        manifest.user_name = self.items['Door43/en_obs']['user_name']
        manifest.load()
        self.assertIsNotNone(manifest.repo_name)
        manifest.delete()
        manifest.load()
        self.assertIsNone(manifest.repo_name)
