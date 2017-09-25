from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
from contextlib import closing

import shutil
from mock import mock
from requests import Response
from libraries.converters.usfm2html_converter import Usfm2HtmlConverter
from libraries.general_tools.file_utils import remove_tree


class TestConverter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='TestConverter')
        self.zip_file = os.path.join(self.resources_dir, '51-PHP.zip')
        self.zip_file = self.make_duplicate_zip_that_can_be_deleted(self.zip_file)

        self.payload = {
            'job': {
                "input_format": "usfm",
                "convert_module": "usfm2html",
                'message': 'Conversion started...',
                'started_at': '2017-03-08T18:57:53Z',
                'errors': [],
                'job_id': '1234587890',
                'method': 'GET',
                'source': 'https://cdn.example.com/preconvert/705948ab00.zip',
                'status': 'started',
                'warnings': [],
                'output_format': 'html',
                'expires_at': '2017-03-09T18:57:51Z',
                'user': 'exampleuser',
                'cdn_file': 'tx/job/1234567890.zip',
                'cdn_bucket': 'test_cdn_bucket',
                "log": ["Started job b07f65d8be71fef116841e5161f3d7f9b69b83673bf72527f1d93186d8869310 at 2017-03-15T17:50:14Z",
                        "Telling module usfm2html to convert https://s3-us-west-2.amazonaws.com/test-tx-webhook/preconvert/acf4d7eaf4.zip and put at https://test-cdn.door43.org/tx/job/b07f65d8be71fef116841e5161f3d7f9b69b83673bf72527f1d93186d8869310.zip"],
                'ended_at': None,
                'success': None,
                'created_at': '2017-03-08T18:57:51Z',
                'callback': 'https://api.example.com/client/callback',
                'eta': '2017-03-08T18:58:11Z',
                'output': 'https://cdn.example.com/tx/job/a07116859e82e4596798cf81349a445e3dcecef463913f762cc5210aebe93db0.zip',
                'identifier': 'richmahn/en-obs/705948ab00',
                'resource_type': 'obs',
                'options': {'pageSize': 'A4'}
            }
        }

    def tearDown(self):
        """Runs after each test."""
        # delete temp files
        remove_tree(self.temp_dir)

    @mock.patch('requests.post')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.convert')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.download_archive')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.upload_archive')
    def test_convert_callback_success(self, mock_upload_archive, mock_download_archive, mock_convert,
                                      mock_request_post):
        # given
        expected_response_code = 200
        mock_download_archive.return_value = True
        mock_upload_archive.return_value = True
        mock_convert.return_value = True
        mock_response = Response()
        mock_response.status_code = expected_response_code
        mock_response.reason = 'OK'
        mock_request_post.return_value = mock_response
        payload = self.payload
        payload['convert_callback'] = 'http://dummy.org'

        # when
        with closing(Usfm2HtmlConverter('', 'dummy_type', self.zip_file, payload=payload)) as tx:
            tx.input_zip_file = self.zip_file
            results = tx.run()

        # then
        self.validate_response(results, tx, expected_response_code)

    @mock.patch('requests.post')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.convert')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.download_archive')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.upload_archive')
    def test_convert_callback_failure(self, mock_upload_archive, mock_download_archive, mock_convert,
                                      mock_request_post):
        # given
        expected_response_code = 504
        mock_download_archive.return_value = True
        mock_upload_archive.return_value = True
        mock_convert.return_value = True
        mock_response = Response()
        mock_response.status_code = expected_response_code
        mock_response.reason = 'Timed out'
        mock_request_post.return_value = mock_response
        payload = self.payload
        payload['convert_callback'] = 'http://dummy.org'

        # when
        with closing(Usfm2HtmlConverter('', 'dummy_type', self.zip_file, payload=payload)) as tx:
            tx.input_zip_file = self.zip_file
            results = tx.run()

        # then
        self.validate_response(results, tx, expected_response_code)

    @mock.patch('requests.post')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.convert')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.download_archive')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.upload_archive')
    def test_convert_callback_invalid_url(self, mock_upload_archive, mock_download_archive, mock_convert,
                                          mock_request_post):
        # given
        expected_response_code = 0
        mock_download_archive.return_value = True
        mock_upload_archive.return_value = True
        mock_convert.return_value = True
        mock_response = Response()
        mock_response.status_code = expected_response_code
        mock_response.reason = 'Timed out'
        mock_request_post.return_value = mock_response
        payload = self.payload
        payload['convert_callback'] = 'dummy.org'

        # when
        with closing(Usfm2HtmlConverter('', 'dummy_type', self.zip_file, payload=payload)) as tx:
            tx.input_zip_file = self.zip_file
            results = tx.run()

        # then
        self.validate_response(results, tx, expected_response_code)

    @mock.patch('requests.post')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.convert')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.download_archive')
    @mock.patch('libraries.converters.usfm2html_converter.Usfm2HtmlConverter.upload_archive')
    def test_convert_callback_missing_job_id(self, mock_upload_archive, mock_download_archive, mock_convert,
                                             mock_request_post):
        # given
        expected_response_code = 200
        mock_download_archive.return_value = True
        mock_upload_archive.return_value = True
        mock_convert.return_value = True
        mock_response = Response()
        mock_response.status_code = expected_response_code
        mock_response.reason = 'OK'
        mock_request_post.return_value = mock_response
        payload = self.payload
        payload['convert_callback'] = 'http://dummy.org'
        del payload['job']['job_id']

        # when
        with closing(Usfm2HtmlConverter('', 'dummy_type', self.zip_file, payload=payload)) as tx:
            tx.input_zip_file = self.zip_file
            results = tx.run()

        # then
        self.validate_response(results, tx, expected_response_code, valid_job_id=False)

    #
    # helpers
    #

    def validate_response(self, results, converter, expected_response_code, valid_job_id=True):
        self.assertEquals(converter.callback_status, expected_response_code)
        self.assertTrue('results' in converter.callback_results)
        self.assertIsNotNone(converter.callback_results['results'])
        self.assertTrue('job_id' in converter.callback_results)
        if valid_job_id:
            self.assertIsNotNone(converter.callback_results['job_id'])
        self.assertEquals(results, converter.callback_results['results'])

    def make_duplicate_zip_that_can_be_deleted(self, zip_file):
        in_zip_file = tempfile.mktemp(prefix="test_data", suffix=".zip", dir=self.temp_dir)
        shutil.copy(zip_file, in_zip_file)
        zip_file = in_zip_file
        return zip_file

if __name__ == '__main__':
    unittest.main()
