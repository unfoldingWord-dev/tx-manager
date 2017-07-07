from __future__ import absolute_import, unicode_literals, print_function
import os
from datetime import datetime
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.general_tools.file_utils import read_file
from libraries.models.manifest import TxManifest


@mock_dynamodb2
class TxManifestTests(TestCase):
    MANIFEST_TABLE_NAME = 'test-manifest'
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        self.db_handler = DynamoDBHandler(TxManifestTests.MANIFEST_TABLE_NAME)
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
            TableName=TxManifestTests.MANIFEST_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'repo_name_lower',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'user_name_lower',
                    'KeyType': 'RANGE'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'repo_name_lower',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_name_lower',
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
            'door43/en_obs': {
                'repo_name_lower': 'en_obs',
                'user_name_lower': 'door43',
                'repo_name': 'en_obs',
                'user_name': 'Door43',
                'lang_code': 'en',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 2,
                'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                'manifest': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')),
                'manifest_lower': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')).lower(),
            },
            'johndoe/en_obs': {
                'repo_name_lower': 'en_obs',
                'user_name_lower': 'johndoe',
                'repo_name': 'en_obs',
                'user_name': 'JohnDoe',
                'lang_code': 'en',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 2,
                'last_updated': '2016-12-21T05:23:01Z',
                'manifest': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')),
                'manifest_lower': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')).lower(),
            },
            'francis/fr_ulb': {
                'repo_name_lower': 'fr_ulb',
                'user_name_lower': 'francis',
                'repo_name': 'fr_ulb',
                'user_name': 'francis',
                'lang_code': 'fr',
                'resource_id': 'ulb',
                'resource_type': 'bundle',
                'title': 'Unlocked Literal Bible',
                'views': 12,
                'last_updated': '2017-02-11T15:43:11Z',
                'manifest': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')),
                'manifest_lower': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')).lower(),
            },
        }

    def populate_table(self):
        for idx in self.items:
            TxManifest(db_handler=self.db_handler).insert(self.items[idx])

    def test_query_manifest(self):
        manifests = TxManifest(db_handler=self.db_handler).query()
        self.assertEqual(len(manifests), len(self.items))
        for manifest in manifests:
            self.assertEqual(manifest.get_db_data(),
                             TxManifest(self.items['{0}/{1}'.format(manifest.user_name_lower,
                                                                    manifest.repo_name_lower)]).get_db_data())

    def test_load_manifest(self):
        # Test loading by just giving it only the repo_name and user_name in the data array in the constructor
        manifest = TxManifest({'repo_name_lower': 'en_obs', 'user_name_lower': 'door43'}, db_handler=self.db_handler)
        self.assertEqual(manifest.get_db_data(), TxManifest(self.items['door43/en_obs']).get_db_data())
        # Test loading by using the load method
        manifest = TxManifest(db_handler=self.db_handler).load({'repo_name_lower': 'en_obs',
                                                                'user_name_lower': 'johndoe'})
        self.assertEqual(manifest.get_db_data(), TxManifest(self.items['johndoe/en_obs']).get_db_data())

    def test_insert_manifest(self):
        # Insert by giving fields in the constructor
        TxManifest({
                'repo_name_lower': 'test_repo1',
                'user_name_lower': 'test_user1',
                'repo_name': 'Test_Repo1',
                'user_name': 'Test_User1',
                'lang_code': 'es',
                'resource_id': 'ta',
                'resource_type': 'man',
                'title': 'translationAcadamy',
                'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            },
            db_handler=self.db_handler).insert()
        manifest = TxManifest(db_handler=self.db_handler).load({'repo_name_lower': 'test_repo1', 'user_name_lower': 'test_user1'})
        self.assertEqual(manifest.resource_id, 'ta')
        # Insert by giving data to the insert() method
        TxManifest(db_handler=self.db_handler).insert({
                'repo_name_lower': 'test_repo2',
                'user_name_lower': 'test_user2',
                'repo_name': 'Test_Repo2',
                'user_name': 'Test_User2',
                'lang_code': 'en',
                'resource_id': 'tn',
                'resource_type': 'help',
                'title': 'translationNotes',
                'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            })
        manifest = TxManifest(db_handler=self.db_handler).load({'repo_name_lower': 'test_repo2',
                                                                'user_name_lower': 'test_user2'})
        self.assertEqual(manifest.resource_id, 'tn')

    def test_update_manifest(self):
        repo_name = self.items['francis/fr_ulb']['repo_name_lower']
        user_name = self.items['francis/fr_ulb']['user_name_lower']
        manifest = TxManifest(db_handler=self.db_handler).load({'repo_name_lower': repo_name,
                                                                'user_name_lower': user_name})
        # Update by setting fields and calling update()
        manifest.resource_id = 'udb'
        manifest.title = 'Unlocked Dynamic Bible'
        manifest.update()
        manifest = TxManifest(db_handler=self.db_handler).load({'repo_name_lower': repo_name,
                                                                'user_name_lower': user_name})
        self.assertEqual(manifest.resource_id, 'udb')
        self.assertEqual(manifest.title, 'Unlocked Dynamic Bible')
        # Update by giving a dict to update()
        manifest.update({'views': 5})
        manifest = TxManifest(db_handler=self.db_handler).load({'repo_name_lower': repo_name,
                                                                'user_name_lower': user_name})
        self.assertEqual(manifest.views, 5)

    def test_delete_manifest(self):
        manifest = TxManifest(db_handler=self.db_handler)
        manifest.repo_name_lower = self.items['door43/en_obs']['repo_name_lower']
        manifest.user_name_lower = self.items['door43/en_obs']['user_name_lower']
        manifest.load()
        self.assertIsNotNone(manifest.repo_name_lower)
        manifest.delete()
        manifest.load()
        self.assertIsNone(manifest.repo_name_lower)
