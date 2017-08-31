from __future__ import absolute_import, unicode_literals, print_function
import os
from datetime import datetime
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.general_tools.file_utils import read_file
from libraries.models.manifest import Manifest
from libraries.db.db import DB


@mock_dynamodb2
class TxManifestTests(TestCase):
    MANIFEST_TABLE_NAME = 'test-manifest'
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        self.db_handler = DynamoDBHandler(self.MANIFEST_TABLE_NAME)
        self.init_table()
        self.items = {}
        self.init_items()
        self.populate_table()

    def init_table(self):
        DB(connection_string='sqlite:///:memory:', default_db=True)

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
            manifest = Manifest(**self.items[idx])
            DB.db.add(manifest)
        DB.db.commit()

    def test_query_manifest(self):
        manifests = DB.db.query(Manifest)
        self.assertEqual(manifests.count(), len(self.items))
        for manifest in manifests:
            self.assertEqual(manifest.resource_id,
                             self.items['{0}/{1}'.format(manifest.user_name, manifest.repo_name)]['resource_id'])

    def test_load_manifest(self):
        manifest_dict = self.items['door43/en_obs']
        # Test loading by just giving it only the repo_name and user_name in the data array in the constructor
        manifest_from_db = DB.db.query(Manifest).filter_by(repo_name=manifest_dict['repo_name'],
                                                             user_name=manifest_dict['user_name']).first()
        self.assertEqual(manifest_from_db.resource_id, manifest_dict['resource_id'])

    def test_insert_manifest(self):
        # Insert by giving fields in the constructor
        manifest = Manifest(
            repo_name='Test_Repo1',
            user_name='Test_User1',
            lang_code='es',
            resource_id='ta',
            resource_type='man',
            title='translationAcadamy',
            last_updated=datetime.utcnow()
        )
        DB.db.add(manifest)
        DB.db.commit()
        manifest_from_db = DB.db.query(Manifest).filter_by(repo_name=manifest.repo_name, user_name=manifest.user_name).first()
        self.assertEqual(manifest_from_db.resource_id, 'ta')

    def test_update_manifest(self):
        repo_name = self.items['francis/fr_ulb']['repo_name']
        user_name = self.items['francis/fr_ulb']['user_name']
        manifest = DB.db.query(Manifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        # Update by setting fields and calling update()
        manifest.resource_id = 'udb'
        manifest.title = 'Unlocked Dynamic Bible'
        DB.db.commit()
        manifest_from_db = DB.db.query(Manifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        self.assertEqual(manifest, manifest_from_db)
        # Update by giving a dict to update()
        manifest.views = 5
        DB.db.commit()
        manifest_from_db = DB.db.query(Manifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        self.assertEqual(manifest_from_db.views, 5)

    def test_delete_manifest(self):
        repo_name = self.items['door43/en_obs']['repo_name']
        user_name = self.items['door43/en_obs']['user_name']
        manifest = DB.db.query(Manifest).filter_by(repo_name=repo_name, user_name=user_name).first()
        self.assertIsNotNone(manifest)
        DB.db.delete(manifest)
        self.assertEqual(DB.db.query(Manifest).filter_by(repo_name=repo_name, user_name=user_name).count(), 0)
