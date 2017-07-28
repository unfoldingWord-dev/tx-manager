from __future__ import absolute_import, unicode_literals, print_function
import datetime
import unittest
from moto import mock_dynamodb2
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.models.language_stats import LanguageStats


@mock_dynamodb2
class ViewCountTest(unittest.TestCase):

    MOCK_LANGUAGE_STATS_TABLE_NAME = 'test_language_stats'
    LANG_CODE = "en"
    INITIAL_VIEW_COUNT = 5

    env_vars = {
        'language_stats_table_name': MOCK_LANGUAGE_STATS_TABLE_NAME
    }

    def setUp(self):
        self.db_handler = DynamoDBHandler(ViewCountTest.MOCK_LANGUAGE_STATS_TABLE_NAME)
        self.init_table(ViewCountTest.INITIAL_VIEW_COUNT)

    def test_valid(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/en/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_validIncrement(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT + 1
        self.lang_url = "https://live.door43.org/en/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_invalidManifestTableShouldFail(self):
        # given
        vc = PageMetrics(**{})
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT + 1
        self.lang_url = "https://live.door43.org/en/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.DB_ACCESS_ERROR)

    def test_validLangNotInManifestTable(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/zzz/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_validLangNotInManifestTableIncrement(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = 1
        self.lang_url = "https://live.door43.org/zzz/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_validLangTextIncrement(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = 1
        self.lang_url = "https://live.door43.org/zzz/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_missingPathShouldFail(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = 0
        self.lang_url = ""

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_unsupportedPathShouldFail(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = 0
        self.lang_url = "https://other_url.com/dummy/stuff2/stuff3/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_missingEnvironmentShouldFail(self):
        # given
        vc = PageMetrics(**{})
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/en/"
        self.db_handler = DynamoDBHandler("dev-" + PageMetrics.MANIFEST_TABLE_NAME)

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.DB_ACCESS_ERROR)

    def test_shortUrlShouldFail(self):
        # given
        vc = PageMetrics(**{})
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/"
        self.db_handler = DynamoDBHandler("dev-" + PageMetrics.LANGUAGE_STATS_TABLE_NAME)

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_shortLanguageShouldFail(self):
        # given
        vc = PageMetrics(**{})
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/e/"
        self.db_handler = DynamoDBHandler("dev-" + PageMetrics.LANGUAGE_STATS_TABLE_NAME)

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/enxx/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail2(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/eng-/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail3(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/eng-a/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail4(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/eng-x/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail5(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/eng-x-/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_extendedLanguage(self):
        # given
        vc = PageMetrics(**ViewCountTest.env_vars)
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/eng-x-a/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    #
    # helpers
    #

    def validateResults(self, expected_view_count, results, error_type=None):
        self.assertIsNotNone(results)
        if error_type:
            self.assertEquals(results['ErrorMessage'], error_type + self.lang_url, "Error message mismatch")
        else:
            self.assertTrue('ErrorMessage' not in results)
            self.assertEquals(results['view_count'], expected_view_count)

    def init_table(self, view_count):
        try:
            self.db_handler.table.delete()
        except:
            pass

        self.db_handler.resource.create_table(
            TableName=ViewCountTest.MOCK_LANGUAGE_STATS_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'lang_code',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'lang_code',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )

        lang_stats_data = {
            'lang_code': ViewCountTest.LANG_CODE.lower(),
            'last_updated': datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'manifest': '{}',
            'views': ViewCountTest.INITIAL_VIEW_COUNT
        }

        lang_stats = LanguageStats(lang_stats_data, db_handler=self.db_handler).insert()
        print("new language: " + lang_stats.lang_code)


if __name__ == "__main__":
    unittest.main()
