from __future__ import absolute_import, unicode_literals, print_function
import unittest
import logging
from libraries.manifest.view_count import ViewCount
from moto import mock_dynamodb2


# @mock_dynamodb2
class ViewCountTest(unittest.TestCase):
    # MOCK_API_URL = 'https://api.example.com'
    # MOCK_CDN_URL = 'https://cdn.example.com'
    # MOCK_CALLBACK_URL = 'https://callback.example.com/'
    # MOCK_GOGS_URL = 'https://mock.gogs.io'
    # MOCK_CDN_BUCKET = 'mock_bucket'
    # MOCK_JOB_TABLE_NAME = 'mock-job'
    # MOCK_MODULE_TABLE_NAME = 'mock-module'
    MOCK_MANIFEST_TABLE_NAME = 'view-count-test-tx-manifest'

    env_vars = {
        'manifest_table_name': MOCK_MANIFEST_TABLE_NAME
    }

    # @unittest.skip("skip")
    def test_live(self):

        # Set required env_vars
        env_vars = { # for dev
            'manifest_table_name': 'test-tx-manifest'
        }

        vc = ViewCount(**env_vars)
        vc.logger.setLevel(logging.INFO)
        expected_view_count = 0

        # repo_url = "https://live.door43.org/u/tx-manager-test-data/awa_act_text_reg/96db55378e/"
        repo_url = "https://live.door43.org/u/tx-manager-test-data/awa_act_text_reg2/96db55378e/"
        results = vc.get_view_count(repo_url, increment=True)
        self.assertIsNotNone(results)
        self.assertTrue('ErrorMessage' not in results)
        self.assertEquals(results['view_count'], str(expected_view_count))

if __name__ == "__main__":
    unittest.main()
