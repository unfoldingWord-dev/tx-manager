from __future__ import absolute_import, unicode_literals, print_function
import unittest
import mock
from libraries.door43_tools.download_metrics import DownloadMetrics
from libraries.lambda_handlers.check_download_handler import CheckDownloadHandler


class CheckDownloadsTest(unittest.TestCase):

    @mock.patch('libraries.door43_tools.download_metrics.DownloadMetrics.check_download')
    def test_check_download(self, mock_check_download):
        mock_check_download.return_value = {
            'download_exists': True
        }
        event = {
            'vars': {
                'pre_convert_bucket': 'test-tx-webhook-client'
            },
            "api-gateway": {
                "params": {
                    'querystring': {
                        'commit_id': '39a099622d'
                    }
                }
            }
        }

        handler = CheckDownloadHandler()
        results = handler.handle(event, None)
        self.assertIsNotNone(results)
        self.assertIsNotNone(results['download_exists'])

if __name__ == "__main__":
    unittest.main()
