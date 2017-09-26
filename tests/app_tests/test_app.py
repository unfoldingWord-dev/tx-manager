from __future__ import absolute_import, unicode_literals, print_function
import unittest
from moto import mock_dynamodb2, mock_s3
from libraries.app.app import App
from libraries.models.tx_model import TxModel
from sqlalchemy import Column, Integer, String


class User(App.Base, TxModel):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)


class TestApp(unittest.TestCase):

    def test_init(self):
        gogs_url = 'https://my.gogs.org'
        App(gogs_url=gogs_url)
        self.assertEqual(App.gogs_url, gogs_url)

    def test_construction_connection_string(self):
        """
        Test the construction of the connection string with multiple attributes
        """
        App(db_protocol='protocol', db_user='user', db_pass='pass', db_end_point='my.endpoint.url', db_port='9999',
            db_name='db', db_connection_string_params='charset=utf8', auto_setup_db=False)
        expected = "protocol://user:pass@my.endpoint.url:9999/db?charset=utf8"
        connection_str = App.construct_connection_string()
        self.assertEqual(connection_str, expected)

    def test_db(self):
        App(db_connection_string='sqlite:///:memory:')
        App.db_create_tables([User.__table__])
        user = User(name='ed', fullname='Edward Scissorhands', password='12345')
        user.insert()
        user_from_db = User.get(name='ed')
        self.assertIsNotNone(user_from_db)
        self.assertEqual(user_from_db.password, '12345')

    def test_setup_db_with_connection_string_parts(self):
        App(db_protocol='sqlite', db_user=None, db_pass=None, db_end_point=None, db_port=None, db_name=':memory:',
            db_connection_string_params=None)
        App.db_create_tables([User.__table__])
        user = User(name='ed', fullname='Edward Scissorhands', password='12345')
        user.insert()
        user_from_db = User.get(name='ed')
        self.assertIsNotNone(user_from_db)
        self.assertEqual(user_from_db.password, '12345')
        App.db_close()

    @mock_s3
    def test_s3_handler(self):
        self.assertIsNotNone(App.cdn_s3_handler())

    @mock_dynamodb2
    def test_dynamodb_handler(self):
        self.assertIsNotNone(App.language_stats_db_handler())

    def test_prefix_vars(self):
        App(prefix='')
        self.assertEqual(App.cdn_bucket, 'cdn.door43.org')
        self.assertEqual(App.api_url, 'https://api.door43.org')
        App(prefix='test-')
        self.assertEqual(App.cdn_bucket, 'test-cdn.door43.org')
        self.assertEqual(App.api_url, 'https://test-api.door43.org')
        App(prefix='test2-')
        self.assertEqual(App.cdn_bucket, 'test2-cdn.door43.org')
        self.assertEqual(App.api_url, 'https://test2-api.door43.org')
        App(prefix='')
        self.assertEqual(App.cdn_bucket, 'cdn.door43.org')
        self.assertEqual(App.api_url, 'https://api.door43.org')

    def test_reset_app(self):
        default_name = App.name
        App(name='test-name')
        App()
        self.assertEqual(App.name, default_name)
        App.name = 'test-name-2'
        App(name='test-name-2', reset=False)
        self.assertNotEqual(App.name, default_name)
