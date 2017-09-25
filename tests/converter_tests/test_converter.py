from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import shutil
from contextlib import closing
from mock import mock
from requests import Response
from libraries.converters.converter import Converter
from libraries.converters.usfm2html_converter import Usfm2HtmlConverter
from libraries.general_tools.file_utils import remove_tree


class MyConverter(Converter):
    def __init__(self, source, resource, cdn_file=None, options=None, convert_callback=None, identity=None):
        super(MyConverter, self).__init__(source, resource, cdn_file=cdn_file, options=options,
                                          convert_callback=convert_callback, identity=identity)
        self.convert_return = None
        self.download_return = None
        self.upload_return = None

    def convert(self):
        return self.convert_return

    def download_archive(self):
        return self.download_return

    def upload_archive(self):
        return self.upload_return


class TestConverter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='TestConverter')
        self.zip_file = os.path.join(self.resources_dir, '51-PHP.zip')
        self.zip_file = self.make_duplicate_zip_that_can_be_deleted(self.zip_file)

        self.params = {
            'cdn_file': 'tx/job/1234567890.zip',
            'identity': 'richmahn/en-obs/705948ab00',
            'source': 'https://cdn.example.com/preconvert/705948ab00.zip',
            'resource_type': 'obs',
            'options': {'pageSize': 'A4'}
        }

    def tearDown(self):
        """Runs after each test."""
        # delete temp files
        remove_tree(self.temp_dir)

    @mock.patch('requests.post')
    def test_convert_callback_success(self, mock_request_post):
        # given
        params = self.params
        params['convert_callback'] = 'http://dummy.org'
        converter = self.get_converter(params)
        expected_response_code = 200
        response_string = 'OK'
        self.get_mock_response(mock_request_post, expected_response_code, response_string)

        # when
        with closing(converter) as tx:
            tx.input_zip_file = self.zip_file
            results = tx.run()

        # then
        self.validate_response(results, tx, expected_response_code)

    @mock.patch('requests.post')
    def test_convert_callback_failure(self, mock_request_post):
        # given
        params = self.params
        params['convert_callback'] = 'http://dummy.org'
        converter = self.get_converter(params)
        expected_response_code = 504
        response_string = 'Timed out'
        self.get_mock_response(mock_request_post, expected_response_code, response_string)
        params = self.params
        params['convert_callback'] = 'http://dummy.org'

        # when
        with closing(converter) as tx:
            tx.input_zip_file = self.zip_file
            results = tx.run()

        # then
        self.validate_response(results, tx, expected_response_code)

    @mock.patch('requests.post')
    def test_convert_callback_invalid_url(self, mock_request_post):
        # given
        params = self.params
        params['convert_callback'] = 'http://dummy.org'
        converter = self.get_converter(params)
        expected_response_code = 0
        response_string = 'Timed out'
        self.get_mock_response(mock_request_post, expected_response_code, response_string)
        params = self.params
        params['convert_callback'] = 'dummy.org'

        # when
        with closing(converter) as tx:
            tx.input_zip_file = self.zip_file
            results = tx.run()

        # then
        self.validate_response(results, tx, expected_response_code)

    @mock.patch('requests.post')
    def test_convert_callback_missing_identity(self, mock_request_post):
        # given
        params = self.params
        params['convert_callback'] = 'http://dummy.org'
        converter = self.get_converter(params)
        expected_response_code = 200
        response_string = 'OK'
        self.get_mock_response(mock_request_post, expected_response_code, response_string)
        params = self.params
        params['convert_callback'] = 'http://dummy.org'
        del params['identity']

        # when
        with closing(converter) as tx:
            tx.input_zip_file = self.zip_file
            results = tx.run()

        # then
        self.validate_response(results, tx, expected_response_code, valid_identity=False)

    #
    # helpers
    #

    def get_mock_response(self, mock_request_post, expected_response_code, response_string):
        mock_response = Response()
        mock_response.status_code = expected_response_code
        mock_response.reason = response_string
        mock_request_post.return_value = mock_response

    def validate_response(self, results, converter, expected_response_code, valid_identity=True):
        self.assertEquals(converter.callback_status, expected_response_code)
        self.assertTrue('results' in converter.callback_results)
        self.assertIsNotNone(converter.callback_results['results'])
        self.assertTrue('identity' in converter.callback_results)
        if valid_identity:
            self.assertIsNotNone(converter.callback_results['identity'])
        self.assertEquals(results, converter.callback_results['results'])

    def make_duplicate_zip_that_can_be_deleted(self, zip_file):
        in_zip_file = tempfile.mktemp(prefix="test_data", suffix=".zip", dir=self.temp_dir)
        shutil.copy(zip_file, in_zip_file)
        zip_file = in_zip_file
        return zip_file

    def get_converter(self, params):
        source = params['source']
        resource = params['resource_type']
        cdn_file = params['cdn_file']
        options = params['options']
        identity = None if 'identity' not in params else params['identity']
        convert_callback = None if 'convert_callback' not in params else params['convert_callback']
        converter = Usfm2HtmlConverter(source, resource, cdn_file=cdn_file, options=options,
                                       convert_callback=convert_callback, identity=identity)
        converter.download_return = True
        converter.upload_return = True
        converter.convert_return = True
        return converter


if __name__ == '__main__':
    unittest.main()
