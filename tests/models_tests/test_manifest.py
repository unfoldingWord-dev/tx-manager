from __future__ import absolute_import, unicode_literals, print_function
import os
from datetime import datetime
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.general_tools.file_utils import read_file
from libraries.models.manifest import TxManifest
from libraries.app.app import App


@mock_dynamodb2
class TxManifestTests(TestCase):
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
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
            tx_manifest.insert()

    def test_query_manifest(self):
        manifests = TxManifest.query()
        self.assertEqual(manifests.count(), len(self.items))
        for tx_manifest in manifests:
            self.assertEqual(tx_manifest.resource_id,
                             self.items['{0}/{1}'.format(tx_manifest.user_name, tx_manifest.repo_name)]['resource_id'])

    def test_load_manifest(self):
        manifest_dict = self.items['Door43/en_obs']
        # Test loading by just giving it only the repo_name and user_name in the data array in the constructor
        manifest_from_db = TxManifest.get(repo_name=manifest_dict['repo_name'],
                                          user_name=manifest_dict['user_name'])
        self.assertEqual(manifest_from_db.resource_id, manifest_dict['resource_id'])

    def test_insert_manifest(self):
        # Insert by giving fields in the constructor
        data = {
            'repo_name': 'Test_Repo1',
            'user_name': 'Test_User1',
            'lang_code': 'es',
            'resource_id': 'ta',
            'resource_type': 'man',
            'title': 'translationAcadamy',
            'last_updated': datetime.utcnow()
        }
        tx_manifest = TxManifest(**data)
        tx_manifest.insert()
        manifest_from_db = TxManifest.get(repo_name=data['repo_name'], user_name=data['user_name'])
        self.assertEqual(manifest_from_db.resource_id, 'ta')

    def test_update_manifest(self):
        repo_name = self.items['francis/fr_ulb']['repo_name']
        user_name = self.items['francis/fr_ulb']['user_name']
        tx_manifest = TxManifest.get(repo_name=repo_name, user_name=user_name)
        # Update by setting fields and calling update()
        tx_manifest.resource_id = 'udb'
        tx_manifest.title = 'Unlocked Dynamic Bible'
        tx_manifest.update()
        manifest_from_db = TxManifest.get(repo_name=repo_name, user_name=user_name)
        self.assertEqual(manifest_from_db.title, tx_manifest.title)
        # Update by giving a dict to update()
        tx_manifest.views = 5
        tx_manifest.update()
        manifest_from_db = TxManifest.get(repo_name=repo_name, user_name=user_name)
        self.assertEqual(manifest_from_db.views, 5)
        App.db_close()

    def test_delete_manifest(self):
        repo_name = self.items['Door43/en_obs']['repo_name']
        user_name = self.items['Door43/en_obs']['user_name']
        tx_manifest = TxManifest.get(repo_name=repo_name, user_name=user_name)
        self.assertIsNotNone(tx_manifest)
        tx_manifest.delete()
        self.assertEqual(TxManifest.query(repo_name=repo_name, user_name=user_name).count(), 0)

    def test_manifest_last_modified_not_auto_updating(self):
        sometime = datetime.strptime('2017-02-11T15:43:11Z', '%Y-%m-%dT%H:%M:%SZ')
        manifest = TxManifest(**{
            'repo_name': 'es_ulb',
            'user_name': 'franco',
            'lang_code': 'es',
            'resource_id': 'ulb',
            'resource_type': 'bundle',
            'title': 'Unlocked Literal Bible',
            'views': 12,
            'last_updated': sometime,
            #'manifest': read_file(os.path.join(self.resources_dir, 'obs_manifest.yaml'))
        })
        manifest.insert()
        manifest_from_db = TxManifest.get(manifest.id)
        self.assertEqual(manifest_from_db.last_updated, sometime)
        manifest.views = manifest.views + 1
        manifest.update()
        manifest_from_db = TxManifest.get(manifest.id)
        self.assertEqual(manifest_from_db.last_updated, sometime)
        manifest.last_updated = datetime.strptime('2018-03-12T15:43:11Z', '%Y-%m-%dT%H:%M:%SZ')
        manifest.update()
        manifest_from_db = TxManifest.get(manifest.id)
        self.assertNotEqual(manifest_from_db.last_updated, sometime)
