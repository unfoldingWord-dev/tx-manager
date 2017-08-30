from __future__ import absolute_import, unicode_literals, print_function
import mock
import unittest
from libraries.aws_tools.sql_db_table_handler import SqlDbTableHandler, Base
from sqlalchemy import Column, Integer, String


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)

    def __repr__(self):
        return "<User(name='%s', fullname='%s', password='%s')>" % (self.name, self.fullname, self.password)


class TestSqlDbHandler(unittest.TestCase):

    def setUp(self):
        """
        Setup ran for every test
        :return:
        """
        self.setup_test_db()

    def setup_test_db(self):
        """
        Setup a test DB that is used for most test cases with SqLite using the User model above
        :return:
        """
        self.user_db_handler = SqlDbTableHandler(User, connection_string='sqlite:///:memory:')
        self.user_db_handler.create_table()
        self.user1 = User(name='jim', fullname='Jim Smith', password='jimspassword')
        self.user2 = User(name='ed', fullname='Ed Jones', password='edspassword')
        self.user3 = User(name='sarah', fullname='Sarah Lee', password='sarahspassword')
        self.user_db_handler.insert_items([self.user1, self.user2, self.user3])

    @mock.patch('libraries.aws_tools.sql_db_table_handler.SqlDbTableHandler.setup_resources')
    def test_connection_string(self, mock_setup_resources):
        """
        Test the construction of the connection string with multiple attributes
        """
        db_handler = SqlDbTableHandler(User, db_protocol='protocol', db_user='user', db_pass='pass',
                                       end_point='my.endpoint.url', db_port='9999', db_name='db',
                                       echo=True)
        expected = "protocol://user:pass@my.endpoint.url:9999/db"
        self.assertEqual(db_handler.connection_string, expected)
        self.assertTrue(db_handler.echo)

    def test_get_item(self):
        """Test a successful invocation of `get_item`."""
        user = self.user_db_handler.get_item({'name': self.user1.name})
        self.assertEqual(user, self.user1)

    def test_query_items(self):
        """Test a successful invocation of `query_items`."""
        results = self.user_db_handler.query_items({'password': '%password'})
        self.assertEqual(results.count(), 3)

    def test_query_items_order_by(self):
        """Test a successful invocation of `query_item` with order_by."""
        results = self.user_db_handler.query_items({'password': '%password'}, User.name)
        self.assertEqual(results.count(), 3)
        self.assertEqual(results[0], self.user2)

    def test_query_item_no_results(self):
        """Test a invocation of `query_item` with no results."""
        results = self.user_db_handler.query_items({'name': 'doesnotexist'})
        self.assertEqual(results.count(), 0)

    def test_insert_item(self):
        """Test a successful invocation of `insert_item`."""
        user = User(name='sally', fullname='Sally Lovett', password='sallysspassword')
        self.user_db_handler.insert_item(user)
        user_from_db = self.user_db_handler.session.query(User).filter_by(name='sally').one()
        self.assertEqual(user_from_db, user)

    def test_update_item(self):
        """Test a successful invocation of `update_item`."""
        self.user1.fullname = 'Edward Scissorhands'
        self.user1.password = 'runswithscissors'
        self.user_db_handler.update_item(self.user1)
        user_from_db = self.user_db_handler.get_item({'name': 'ed'})
        self.assertEqual(user_from_db, self.user2)
        self.assertEqual(self.user_db_handler.session.query(User).filter_by(name='ed').count(), 1)

    def test_delete_item(self):
        """Test a successful invocation of `delete_item`."""
        self.user_db_handler.delete_item(self.user1)
        self.assertEqual(self.user_db_handler.session.query(User).filter_by(name=self.user1.name).count(), 0)
