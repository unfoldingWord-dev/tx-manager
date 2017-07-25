from __future__ import absolute_import, unicode_literals, print_function
import json
import mock
from decimal import Decimal
from unittest import TestCase
from libraries.lambda_handlers.language_view_count_handler import LanguageViewCountHandler


class LanguageViewCountHandlerTest(TestCase):

    SUPPORTED_PATH = 'https://live.door43.org/en/'

    def setUp(self):
        self.return_view_count = 0
        self.error_response = None

    @mock.patch('libraries.door43_tools.page_metrics.PageMetrics.get_language_count')
    def test_handle(self, mock_get_language_count):
        # given
        mock_get_language_count.side_effect = self.mock_get_language_count
        increment = 0
        path = LanguageViewCountHandlerTest.SUPPORTED_PATH
        callback = 'cb'
        return_view_count = 1234
        event = self.initialize_test(callback, path, increment, return_view_count)
        handler = LanguageViewCountHandler()

        # when
        response = handler.handle(event, None)

        # then
        self.validate_results(response)

    @mock.patch('libraries.door43_tools.page_metrics.PageMetrics.get_language_count')
    def test_handleNoIncrement(self, mock_get_language_count):
        # given
        mock_get_language_count.side_effect = self.mock_get_language_count
        increment = None
        path = LanguageViewCountHandlerTest.SUPPORTED_PATH
        callback = 'cb'
        return_view_count = 1234
        event = self.initialize_test(callback, path, increment, return_view_count)
        handler = LanguageViewCountHandler()

        # when
        response = handler.handle(event, None)

        # then
        self.validate_results(response)

    @mock.patch('libraries.door43_tools.page_metrics.PageMetrics.get_language_count')
    def test_handleIncrement(self, mock_get_language_count):
        # given
        mock_get_language_count.side_effect = self.mock_get_language_count
        increment = 1
        path = LanguageViewCountHandlerTest.SUPPORTED_PATH
        callback = 'cb'
        return_view_count = 1234
        event = self.initialize_test(callback, path, increment, return_view_count)
        handler = LanguageViewCountHandler()
        self.expected_view_count = return_view_count + 1  # expect incremented count

        # when
        response = handler.handle(event, None)

        # then
        self.validate_results(response)

    @mock.patch('libraries.door43_tools.page_metrics.PageMetrics.get_language_count')
    def test_handleError(self, mock_get_language_count):
        # given
        mock_get_language_count.side_effect = self.mock_get_language_count
        increment = 1
        path = LanguageViewCountHandlerTest.SUPPORTED_PATH
        callback = 'cb'
        return_view_count = 1234
        error_response = "ERROR!!"

        event = self.initialize_test(callback, path, increment, return_view_count, error_response)
        handler = LanguageViewCountHandler()
        self.expected_view_count = return_view_count + 1  # expect incremented count

        # when
        response = handler.handle(event, None)

        # then
        self.validate_results(response)

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
            self.assertEqual(self.expected_view_count, data['view_count'])

    def initialize_test(self, callback, path, increment, return_value, error_response=None):
        query_string = {}
        if callback:
            query_string['callback'] = callback
        if path:
            query_string['path'] = path
        if increment is not None:
            query_string['increment'] = str(increment)
        event = {
            'data': {},
            'body-json': {},
            'vars': {
                'language_stats_table_name': 'test-language-stats'
            },
            'api-gateway': {
                'params': {
                    'querystring': query_string
                }
            }
        }
        self.callback = callback
        self.error_response = error_response
        self.expected_view_count = return_value
        self.return_view_count = Decimal(return_value)
        return event

    def mock_get_language_count(self, path, increment=0):
        if self.error_response:
            response = {
                'ErrorMessage': self.error_response
            }
            return response

        view_count = self.return_view_count
        if increment:
            view_count += 1
        if type(view_count) is Decimal:
            view_count = int(view_count.to_integral_value())
        response = {
            'view_count': view_count
        }
        return response

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
