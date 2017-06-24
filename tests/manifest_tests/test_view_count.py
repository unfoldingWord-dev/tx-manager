from __future__ import absolute_import, unicode_literals, print_function
import unittest
import datetime
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.manifest.view_count import ViewCount
from moto import mock_dynamodb2

from libraries.models.manifest import TxManifest


@mock_dynamodb2
class ViewCountTest(unittest.TestCase):

    MOCK_MANIFEST_TABLE_NAME = 'view-count-test-tx-manifest'
    USER_NAME = "dummy"
    REPO_NAME = "repo"
    INITIAL_VIEW_COUNT = 5

    env_vars = {
        'manifest_table_name': MOCK_MANIFEST_TABLE_NAME
    }

    def setUp(self):
        self.db_handler = DynamoDBHandler(ViewCountTest.MOCK_MANIFEST_TABLE_NAME)
        self.init_table(ViewCountTest.INITIAL_VIEW_COUNT)

    def test_valid(self):
        # given
        vc = ViewCount(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.repo_url = "https://live.door43.org/u/dummy/repo/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_validIncrement(self):
        # given
        vc = ViewCount(**ViewCountTest.env_vars)
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT + 1
        self.repo_url = "https://live.door43.org/u/dummy/repo/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_validInvalidManifestTable(self):
        # given
        vc = ViewCount(**{})
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT + 1
        self.repo_url = "https://live.door43.org/u/dummy/repo/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=ViewCount.DB_ACCESS_ERROR)

    def test_validRepoNotInManifestTable(self):
        # given
        vc = ViewCount(**ViewCountTest.env_vars)
        expected_view_count = 0
        self.repo_url = "https://live.door43.org/u/dummy/repo2/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_validRepoNotInManifestTableIncrement(self):
        # given
        vc = ViewCount(**ViewCountTest.env_vars)
        expected_view_count = 0
        self.repo_url = "https://live.door43.org/u/dummy/repo2/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    #
    # helpers
    #

    def validateResults(self, expected_view_count, results, error_type=None):
        self.assertIsNotNone(results)
        if error_type:
            self.assertEquals(results['ErrorMessage'], error_type + self.repo_url, "Error message mismatch" )
        else:
            self.assertTrue('ErrorMessage' not in results)
            self.assertEquals(results['view_count'], expected_view_count)

    def init_table(self, view_count):
        try:
            self.db_handler.table.delete()
        except:
            pass

        self.db_handler.resource.create_table(
            TableName=ViewCountTest.MOCK_MANIFEST_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'repo_name',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'user_name',
                    'KeyType': 'RANGE'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'repo_name',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'user_name',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )

        manifest_data = {
            'repo_name': ViewCountTest.REPO_NAME,
            'user_name': ViewCountTest.USER_NAME,
            'lang_code': 'lang',
            'resource_id': 'redID',
            'resource_type': 'resType',
            'title': 'title',
            'last_updated': datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'manifest': '{}',
            'views': ViewCountTest.INITIAL_VIEW_COUNT
        }

        tx_manifest = TxManifest(manifest_data, db_handler=self.db_handler).insert()
        print("new repo: " + tx_manifest.repo_name)


if __name__ == "__main__":
    unittest.main()
