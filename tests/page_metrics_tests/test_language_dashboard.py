from __future__ import absolute_import, unicode_literals, print_function
import unittest

from bs4 import BeautifulSoup
from moto import mock_dynamodb2

from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.manager.manager import TxManager
from libraries.models.language_stats import LanguageStats


@mock_dynamodb2
class LanguageDashboardTest(unittest.TestCase):
    MOCK_LANGUAGE_TABLE_NAME = 'test-language-stats_dummy'

    tx_manager_env_vars = {
        'language_stats_table_name': MOCK_LANGUAGE_TABLE_NAME
    }

    def setUp(self):
        self.tx_manager = TxManager(**self.tx_manager_env_vars)
        self.lang_stats_table_name = LanguageDashboardTest.MOCK_LANGUAGE_TABLE_NAME
        self.lang_stats_db_handler = DynamoDBHandler(self.lang_stats_table_name)

        try:
            self.lang_stats_db_handler.table.delete()
        except:
            pass

        self.lang_stats_db_handler.resource.create_table(
            TableName=self.lang_stats_table_name,
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
        )

    def test_build_language_popularity_tables_empty(self):
        # given
        max_count = 10
        tx_manager = TxManager(**self.tx_manager_env_vars)
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.build_language_popularity_tables(body, max_count)

        # then
        self.assertEquals(len(tx_manager.language_views), 0)
        self.assertEquals(len(tx_manager.language_dates), 0)

    def test_build_language_popularity_tables_ten_items(self):
        # given
        max_count = 10
        self.initialze_lang_stats_table(max_count)
        tx_manager = TxManager(**self.tx_manager_env_vars)
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.build_language_popularity_tables(body, max_count)

        # then
        self.assertEquals(len(tx_manager.language_views), 10)
        self.assertEquals(len(tx_manager.language_dates), 10)

    def test_generate_most_recent_lang_table(self):
        # given
        max_count = 5
        item_count = 10
        self.get_view_items(item_count)
        tx_manager = TxManager(**self.tx_manager_env_vars)
        body = BeautifulSoup('<h1>Languages</h1>', 'html.parser')

        # when
        tx_manager.generate_most_recent_lang_table(body, self.language_dates, max_count)

        # then
        self.assertEquals(len(tx_manager.language_views), 0)
        self.assertEquals(len(tx_manager.language_views), 0)

    def initialze_lang_stats_table(self, count):
        for i in range(0, count):
            lang_code = 'xyz-' + str(i+100)
            lang_stat = LanguageStats({}, db_handler=self.lang_stats_db_handler)
            lang_stat.lang_code = lang_code
            lang_stat.last_updated = '2017-02-11T15:43:11.{0}Z'.format(i+1)
            lang_stat.views = i + 1100
            lang_stat.update()

    def get_view_items(self, count):
        self.initialze_lang_stats_table(count)
        vc = PageMetrics(language_stats_table_name=self.lang_stats_table_name)
        vc.init_language_stats_table(None)
        self.language_views = vc.get_language_views_sorted_by_count()
        self.language_dates = vc.get_language_views_sorted_by_date()


if __name__ == "__main__":
    unittest.main()
