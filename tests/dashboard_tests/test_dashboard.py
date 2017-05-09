import unittest

import botocore
import logging

from manager.manager import TxManager


class DashboardTest(unittest.TestCase):

    def test_setup_job(self):

        # Set required env_vars
        env_vars = {
            'api_url': 'https://test-api.door43.org',
            'gogs_url': 'https://git.door43.org',
            'cdn_url': 'https://test-cdn.door43.org',
            'job_table_name': 'test-tx-job',
            'module_table_name': 'test-tx-module'
        }

        tx_manager = TxManager(**env_vars)
        tx_manager.logger.setLevel(logging.INFO)
        dashboard = tx_manager.generate_dashboard()
        body_ = dashboard['body']
        self.assertTrue(isinstance(body_, str))
        length = len(body_)
        self.assertTrue(length > 25)

if __name__ == "__main__":
    unittest.main()
