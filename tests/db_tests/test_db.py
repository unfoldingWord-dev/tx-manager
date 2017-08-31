from __future__ import absolute_import, unicode_literals, print_function
import mock
import unittest
from libraries.db.db import DB
from sqlalchemy import Column, Integer, String
from libraries.models.manifest import Manifest
from datetime import datetime


class User(DB.Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)

    def __repr__(self):
        return "<User(name='%s', fullname='%s', password='%s')>" % (self.name, self.fullname, self.password)


class TestDb(unittest.TestCase):

    @mock.patch('libraries.db.db.DB.setup_resources')
    def test_connection_string(self, mock_setup_resources):
        """
        Test the construction of the connection string with multiple attributes
        """
        my_db = DB(db_protocol='protocol', db_user='user', db_pass='pass', end_point='my.endpoint.url',
                   db_port='9999', db_name='db', echo=True, create_tables=False)
        expected = "protocol://user:pass@my.endpoint.url:9999/db"
        self.assertEqual(my_db.connection_string, expected)

    def test_manifest(self):
        DB(connection_string='sqlite:///:memory:', default_db=True)
        manifest = DB.db.query(Manifest).filter_by(repo_name='en_obs', user_name='Door43').first()
        self.assertIsNone(manifest)
        manifest_data = {
            'repo_name': 'en_obs',
            'user_name': 'Door43',
            'lang_code': 'en',
            'resource_id': 'obs',
            'resource_type': 'book',
            'title': 'OBS',
            'last_updated': datetime.utcnow(),
            'manifest': '{}',
        }
        manifest = Manifest(**manifest_data)
        print(manifest.title)
        DB.db.add(manifest)
        DB.db.commit()
        manifest_from_db = DB.db.query(Manifest).filter_by(repo_name='en_obs', user_name='Door43').first()
        self.assertEqual(manifest, manifest_from_db)
        print(manifest_from_db.title)
