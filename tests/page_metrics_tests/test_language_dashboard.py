from __future__ import absolute_import, unicode_literals, print_function
import unittest
from bs4 import BeautifulSoup
from moto import mock_dynamodb2
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.manager.manager import TxManager
from libraries.models.language_stats import LanguageStats
from libraries.app.app import App


@mock_dynamodb2
class LanguageDashboardTest(unittest.TestCase):

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        self.tx_manager = TxManager()
        self.searches = None
        self.language_views = None

        try:
            App.language_stats_db_handler().table.delete()
        except:
            pass

        App.language_stats_db_handler().resource.create_table(
            TableName=App.language_stats_table_name,
            KeySchema=[
                {
                    'AttributeName': 'lang_code',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'lang_code',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'search_type-views-index',
                    'KeySchema': [
                        {
                            'AttributeName': 'search_type',
                            'KeyType': 'HASH'
                        },
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 123,
                        'WriteCapacityUnits': 123
                    }
                },
            ],
        )

    def tearDown(self):
        """Runs after each test."""
        App.db_close()

    def test_build_language_popularity_tables_empty(self):
        # given
        max_count = 10
        tx_manager = TxManager()
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.build_language_popularity_tables(body, max_count)

        # then
        self.assertEquals(len(tx_manager.language_views), 0)
        self.assertEqual(tx_manager.searches, [])

    def test_build_language_popularity_tables_ten_items(self):
        # given
        max_count = 10
        self.initialze_lang_stats_table(max_count)
        tx_manager = TxManager()
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.build_language_popularity_tables(body, max_count)

        # then
        self.assertEquals(len(tx_manager.language_views), max_count)
        self.assertEqual(tx_manager.searches, [])

    def test_build_search_popularity_tables_ten_items(self):
        # given
        max_count = 10
        self.initialze_searches_table(max_count)
        tx_manager = TxManager()
        body = BeautifulSoup('<h1>Searches</h1>', 'html.parser')

        # when
        tx_manager.build_language_popularity_tables(body, max_count)

        # then
        self.assertEquals(len(tx_manager.searches), max_count)
        self.assertEqual(tx_manager.language_views, [])

    def test_build_language_popularity_tables_invalid_table_name(self):
        # given
        max_count = 10
        tx_manager = TxManager()
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.build_language_popularity_tables(body, max_count)

        # then
        self.assertEqual(tx_manager.language_views, [])
        self.assertEqual(tx_manager.searches, [])

    def test_build_language_popularity_tables_no_table_name(self):
        # given
        max_count = 10
        tx_manager = TxManager()
        tx_manager.language_stats_table_name = 'dummy'
        tx_manager.lang_stats_db_handler = None
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.build_language_popularity_tables(body, max_count)

        # then
        self.assertEqual(tx_manager.language_views, [])
        self.assertEqual(tx_manager.searches, [])

    def test_generate_highest_views_lang_table(self):
        # given
        max_count = 6
        item_count = 10
        self.get_language_view_items(item_count)
        tx_manager = TxManager()
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.generate_highest_views_lang_table(body, self.language_views, max_count)

        # then
        table_id = 'language-popularity'
        row_id = 'popular-'
        self.validate_table(body, table_id, row_id, max_count)

    def test_generate_highest_views_search_table(self):
        # given
        max_count = 6
        item_count = 10
        self.get_search_items(item_count)
        tx_manager = TxManager()
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.generate_highest_searches_table(body, self.searches, max_count)

        # then
        table_id = 'search-popularity'
        row_id = 'popular-'
        self.validate_table(body, table_id, row_id, max_count)

    #
    # helpers
    #

    def validate_table(self, body, table_id, row_id, expected_count):
        html = body.prettify('UTF-8')
        soup = BeautifulSoup(html, 'html.parser')
        language_recent_table = soup.find('table', id=table_id)
        rows = language_recent_table.findAll('tr', id=lambda x: x and x.startswith(row_id))
        row_count = len(rows)
        self.assertEquals(row_count, expected_count)

    def initialze_lang_stats_table(self, count):
        for i in range(0, count):
            lang_code = 'xyz-' + str(i+100)
            lang_stat = LanguageStats({})
            lang_stat.lang_code = lang_code
            lang_stat.last_updated = '2017-02-11T15:43:11.{0}Z'.format(i+1)
            lang_stat.views = i + 1100
            lang_stat.update()

    def initialze_searches_table(self, count):
        for i in range(0, count):
            search = '?lc=en' + str(i+1)
            lang_stat = LanguageStats({})
            lang_stat.lang_code = search
            lang_stat.last_updated = '2017-02-11T15:43:11.{0}Z'.format(i+1)
            lang_stat.views = i + 20
            lang_stat.search_type = 'Y'
            lang_stat.update()

    def get_language_view_items(self, count):
        self.initialze_lang_stats_table(count)
        vc = PageMetrics()
        self.language_views = vc.get_language_views_sorted_by_count()

    def get_search_items(self, count):
        self.initialze_searches_table(count)
        vc = PageMetrics()
        self.searches = vc.get_searches_sorted_by_count()


if __name__ == "__main__":
    unittest.main()
