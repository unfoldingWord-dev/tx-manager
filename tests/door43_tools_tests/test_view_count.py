from __future__ import absolute_import, unicode_literals, print_function
import unittest
from datetime import datetime
from moto import mock_dynamodb2
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.models.manifest import TxManifest
from libraries.db.db import DB


class ViewCountTest(unittest.TestCase):

    USER_NAME = "dummy"
    REPO_NAME = "repo"
    INITIAL_VIEW_COUNT = 5

    def setUp(self):
        self.init_table(ViewCountTest.INITIAL_VIEW_COUNT)

    def init_table(self, view_count):
        DB(connection_string='sqlite:///:memory:', default_db=True)
        tx_manifest = TxManifest(
            repo_name=ViewCountTest.REPO_NAME,
            user_name=ViewCountTest.USER_NAME,
            lang_code='lang',
            resource_id='redID',
            resource_type='resType',
            title='title',
            last_updated=datetime.utcnow(),
            manifest='{}',
            views=view_count
        )
        DB.session.add(tx_manifest)
        DB.session.commit()

    def test_valid(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.repo_url = "https://live.door43.org/u/dummy/repo/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_validIncrement(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT + 1
        self.repo_url = "https://live.door43.org/u/dummy/repo/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_validRepoNotInManifestTable(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.repo_url = "https://live.door43.org/u/dummy/repo2/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_validRepoNotInManifestTableIncrement(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.repo_url = "https://live.door43.org/u/dummy/repo2/96db55378e/"

        # when
        results = vc.get_view_count(self.repo_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_missingPath(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.repo_url = ""

        # when
        results = vc.get_view_count(self.repo_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_URL_ERROR)

    def test_unsupportedPath(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.repo_url = "https://other_url.com/dummy/stuff2/stuff3/"

        # when
        results = vc.get_view_count(self.repo_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_URL_ERROR)

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


if __name__ == "__main__":
    unittest.main()
