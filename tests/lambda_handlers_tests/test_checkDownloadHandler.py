from __future__ import absolute_import, unicode_literals, print_function
import json
import unittest
from libraries.door43_tools.download_metrics import DownloadMetrics
from libraries.lambda_handlers.check_download_handler import CheckDownloadHandler
from moto import mock_s3
from libraries.app.app import App


@mock_s3
class CheckDownloadsTest(unittest.TestCase):

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        App.pre_convert_s3_handler.create_bucket()

    def test_check_present_download(self):
        # given
        commit_id = '39a099622d'
        key = 'preconvert/' + commit_id + '.zip'
        App.cdn_s3_handler.put_contents(key, "dummy")
        exists = App.cdn_s3_handler.key_exists(key)
        self.callback = 'callback'
        event = {
            'data': {
                'commit_id': commit_id,
                'callback': self.callback
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
            'data': {
                 'commit_id': commit_id,
                 'callback': self.callback
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
            'data': {
                'commit_id': commit_id,
                'callback': self.callback
            }
        }
        self.expected_download_exists = False
        self.error_response = DownloadMetrics.ACCESS_FAILED_ERROR + commit_id
        handler = CheckDownloadHandler()

        # when
        results = handler.handle(event, None)

        # then
        self.validate_results(results)

    def test_check_access_error(self):
        # given
        commit_id = '39a099622d'
        self.callback = 'callback'
        event = {
            'vars': {
                'pre_convert_bucket': 'invalid-bucket'
            },
            'data': {
                'commit_id': commit_id,
                'callback': self.callback
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
