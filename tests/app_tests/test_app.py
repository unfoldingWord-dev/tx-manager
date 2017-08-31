from __future__ import absolute_import, unicode_literals, print_function
import unittest
from libraries.app.app import App
from sqlalchemy import Column, Integer, String


class User(App.ModelBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)

    def __repr__(self):
        return "<User(name='%s', fullname='%s', password='%s')>" % (self.name, self.fullname, self.password)


class TestApp(unittest.TestCase):

    def test_init(self):
        App(dcs_ip_address='198.167.2.2')
        self.assertEqual(App.dcs_ip_address, '198.167.2.2')

    def test_construction_connection_string(self):
        """
        Test the construction of the connection string with multiple attributes
        """
        App(db_protocol='protocol', db_user='user', db_pass='pass', db_end_point='my.endpoint.url', db_port='9999',
            db_name='db')
        expected = "protocol://user:pass@my.endpoint.url:9999/db"
        connection_str = App.construct_connection_string()
        self.assertEqual(connection_str, expected)

    def test_setup_db(self):
        App(db_connection_string='sqlite:///:memory:')
        App.setup_db()
        user = User(name='ed', fullname='Edward Scissorhands', password='12345')
        App.db.add(user)
        App.db.commit()
        user_from_db = App.db.query(User).filter_by(name='ed').first()
        self.assertIsNotNone(user_from_db)
        self.assertEqual(user_from_db.password, '12345')
