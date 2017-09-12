from __future__ import absolute_import, unicode_literals, print_function
import os
from datetime import datetime
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.general_tools.file_utils import read_file
from libraries.models.manifest import TxManifest
from libraries.app.app import App


@mock_dynamodb2
class TxManifestTests(TestCase):
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        self.init_table()
        self.items = {}
        self.init_items()
        self.populate_table()

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
                'last_updated': datetime.utcnow(),
                'manifest': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')),
            },
            'JohnDoe/en_obs': {
                'repo_name': 'en_obs',
                'user_name': 'JohnDoe',
                'lang_code': 'en',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 2,
                'last_updated': datetime.strptime('2016-12-21T05:23:01Z', '%Y-%m-%dT%H:%M:%SZ'),
                'manifest': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')),
            },
            'francis/fr_ulb': {
                'repo_name': 'fr_ulb',
                'user_name': 'francis',
                'lang_code': 'fr',
                'resource_id': 'ulb',
                'resource_type': 'bundle',
                'title': 'Unlocked Literal Bible',
                'views': 12,
                'last_updated': datetime.strptime('2017-02-11T15:43:11Z', '%Y-%m-%dT%H:%M:%SZ'),
                'manifest': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml')),
            },
        }

    def populate_table(self):
        for idx in self.items:
            tx_manifest = TxManifest(**self.items[idx])
            App.db.add(tx_manifest)
        App.db.commit()

    def test_query_manifest(self):
        manifests = App.db.query(TxManifest)
        self.assertEqual(manifests.count(), len(self.items))
        for tx_manifest in manifests:
            self.assertEqual(tx_manifest.resource_id,
                             self.items['{0}/{1}'.format(tx_manifest.user_name, tx_manifest.repo_name)]['resource_id'])

    def test_load_manifest(self):
        manifest_dict = self.items['Door43/en_obs']
        # Test loading by just giving it only the repo_name and user_name in the data array in the constructor
        manifest_from_db = App.db.query(TxManifest).filter_by(repo_name=manifest_dict['repo_name'],
                                                              user_name=manifest_dict['user_name']).first()
        self.assertEqual(manifest_from_db.resource_id, manifest_dict['resource_id'])

    def test_insert_manifest(self):
        # Insert by giving fields in the constructor
        tx_manifest = TxManifest(
            repo_name='Test_Repo1',
            user_name='Test_User1',
            lang_code='es',
            resource_id='ta',
            resource_type='man',
            title='translationAcadamy',
            last_updated=datetime.utcnow()
        )
        App.db.add(tx_manifest)
        App.db.commit()
        manifest_from_db = App.db.query(TxManifest).filter_by(repo_name=tx_manifest.repo_name,
                                                              user_name=tx_manifest.user_name).first()
        self.assertEqual(manifest_from_db.resource_id, 'ta')

    def test_update_manifest(self):
        repo_name = self.items['francis/fr_ulb']['repo_name']
        user_name = self.items['francis/fr_ulb']['user_name']
        tx_manifest = App.db.query(TxManifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        # Update by setting fields and calling update()
        tx_manifest.resource_id = 'udb'
        tx_manifest.title = 'Unlocked Dynamic Bible'
        App.db.commit()
        manifest_from_db = App.db.query(TxManifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        self.assertEqual(tx_manifest, manifest_from_db)
        # Update by giving a dict to update()
        tx_manifest.views = 5
        App.db.commit()
        manifest_from_db = App.db.query(TxManifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        self.assertEqual(manifest_from_db.views, 5)

    def test_delete_manifest(self):
        repo_name = self.items['Door43/en_obs']['repo_name']
        user_name = self.items['Door43/en_obs']['user_name']
        tx_manifest = App.db.query(TxManifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        self.assertIsNotNone(tx_manifest)
        App.db.delete(tx_manifest)
        self.assertEqual(App.db.query(TxManifest).filter_by(repo_name=repo_name, user_name=user_name).count(), 0)
