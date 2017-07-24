from __future__ import absolute_import, unicode_literals, print_function

import json
import unittest

from libraries.aws_tools.s3_handler import S3Handler
from libraries.door43_tools.download_metrics import DownloadMetrics
from libraries.lambda_handlers.check_download_handler import CheckDownloadHandler
from moto import mock_s3

@mock_s3
class CheckDownloadsTest(unittest.TestCase):
    MOCK_BUCKET_NAME = "test-bucket"

    def setUp(self):
        self.handler = S3Handler(bucket_name=self.MOCK_BUCKET_NAME)
        self.handler.create_bucket()

    def test_check_present_download(self):
        # given
        commit_id = '39a099622d'
        key = 'preconvert/' + commit_id + '.zip'
        self.handler.put_contents(key, "dummy")
        exists = self.handler.key_exists(key)
        self.callback = 'callback'
        event = {
            'vars': {
                'pre_convert_bucket': self.MOCK_BUCKET_NAME
            },
            "api-gateway": {
                "params": {
                    'querystring': {
                        'commit_id': commit_id,
                        'callback': self.callback
                    }
                }
            }
        }
        self.expected_download_exists = True
        self.error_response = None
        handler = CheckDownloadHandler()

        # when
        results = handler.handle(event, None)

        # then
        self.validate_results(results)

    def test_check_missing_download(self):
        # given
        commit_id = '39a099622d'
        self.callback = 'callback'
        event = {
            'vars': {
                'pre_convert_bucket': self.MOCK_BUCKET_NAME
            },
            "api-gateway": {
                "params": {
                    'querystring': {
                        'commit_id': commit_id,
                        'callback': self.callback
                    }
                }
            }
        }
        self.expected_download_exists = False
        self.error_response = None
        handler = CheckDownloadHandler()

        # when
        results = handler.handle(event, None)

        # then
        self.validate_results(results)

    def test_check_invalid_download(self):
        # given
        commit_id = ''
        self.callback = 'callback'
        event = {
            'vars': {
                'pre_convert_bucket': self.MOCK_BUCKET_NAME
            },
            "api-gateway": {
                "params": {
                    'querystring': {
                        'commit_id': commit_id,
                        'callback': self.callback
                    }
                }
            }
        }
        self.expected_download_exists = False
        self.error_response = DownloadMetrics.ACCESS_FAILED_ERROR + commit_id
        handler = CheckDownloadHandler()

        # when
        results = handler.handle(event, None)

        # then
        self.validate_results(results)

    #
    # helpers
    #

    def validate_results(self, response):
        callback, data, valid_jsonp = self.parse_jsonp(response)
        self.assertEqual(self.callback, callback)
        self.assertTrue(valid_jsonp)
        if self.error_response:
            self.assertEqual(self.error_response, data['ErrorMessage'])
        else:
            self.assertEqual(self.expected_download_exists, data['download_exists'])

    def parse_jsonp(self, text):
        valid = False
        callback = None
        data = None
        try:
            prefix = text.split('(')
            dummy_test = '__'
            payload = (prefix[1] + dummy_test).split(')')
            callback = prefix[0]
            data = json.loads(payload[0])
            valid = (payload[1] == dummy_test) and (len(data) > 0)
        except:
            pass

        return callback, data, valid
