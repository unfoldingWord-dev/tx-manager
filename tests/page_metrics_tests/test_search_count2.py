from __future__ import absolute_import, unicode_literals, print_function
import unittest
from datetime import datetime
from moto import mock_dynamodb2
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.models.language_stats import LanguageStats
from libraries.app.app import App


@mock_dynamodb2
class SearchCountTest(unittest.TestCase):

    INITIAL_VIEW_COUNT = 5

    def setUp(self):
        """Runs before test."""
        self.init_table()

    def test_valid(self):
        # given
        vc = PageMetrics()
        expected_view_count = self.INITIAL_VIEW_COUNT + 1
        self.repo_url = "https://api.door43.org?lc=en"

        # when
        results = vc.increment_search_params(self.repo_url)

        # then
        self.assertEquals(expected_view_count, results)

    def test_validRepoNotInManifestTable(self):
        # given
        vc = PageMetrics()
        expected_view_count = 1
        self.repo_url = "https://api.door43.org?lc=en1"

        # when
        results = vc.increment_search_params(self.repo_url)

        # then
        self.assertEquals(expected_view_count, results)

    def test_validRepoNotInManifestTableCallTwice(self):
        # given
        vc = PageMetrics()
        expected_view_count = 2
        self.repo_url = "https://api.door43.org?lc=en1"

        # when
        results = vc.increment_search_params(self.repo_url)
        results = vc.increment_search_params(self.repo_url)

        # then
        self.assertEquals(expected_view_count, results)

    def test_missingPath(self):
        # given
        vc = PageMetrics()
        expected_view_count = -1
        self.repo_url = "https://api.door43.org"

        # when
        results = vc.increment_search_params(self.repo_url)

        # then
        self.assertEquals(expected_view_count, results)

    def test_unsupportedPath(self):
        # given
        vc = PageMetrics()
        expected_view_count = -1
        self.repo_url = "https://api.door43.org?"

        # when
        results = vc.increment_search_params(self.repo_url)

        # then
        self.assertEquals(expected_view_count, results)

    #
    # helpers
    #

    @staticmethod
    def update_lang_stats(lang_stats):
        """
        update the entry in the database
        :param lang_stats:
        :return:
        """
        utcnow = datetime.utcnow()
        lang_stats.last_updated = utcnow.strftime("%Y-%m-%dT%H:%M:%SZ")
        lang_stats.update()

    def init_table(self):
        try:
            handler = App.language_stats_db_handler()
            handler.table.delete()
        except Exception as e:
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
        )
        lang_stats_data = {
            'lang_code': '?lc=en',
            'last_updated': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'search_type': 'Y',
            'views': SearchCountTest.INITIAL_VIEW_COUNT
        }
        lang_stats = LanguageStats(lang_stats_data).insert()


if __name__ == "__main__":
    unittest.main()
