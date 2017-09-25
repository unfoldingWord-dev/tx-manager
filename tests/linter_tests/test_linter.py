from __future__ import absolute_import, unicode_literals, print_function
import os

from mock import mock
from requests import Response

from tests.linter_tests.linter_unittest import LinterTestCase
from libraries.linters.linter import Linter


class MyLinter(Linter):
    def __init__(self, source_zip_url=None, source_zip_file=None, source_dir=None, commit_data=None,
                 lint_callback=None, identity=None, **kwargs):
        super(MyLinter, self).__init__(source_zip_url=source_zip_url, source_zip_file=source_zip_file,
                                       source_dir=source_dir, commit_data=commit_data,
                                       lint_callback=lint_callback, identity=identity, **kwargs)
        self.lint_warning_count = 1
        self.download_return = None
        self.mock_download = False

    def lint(self):
        for i in range(0, self.lint_warning_count):
            self.log.warning('warning')

    def download_archive(self):
        if self.mock_download:
            return self.download_return
        else:
            super(MyLinter, self).download_archive()


class TestLinter(LinterTestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def test_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Linter, None)

    def test_run(self):
        linter = MyLinter(source_zip_file=os.path.join(self.resources_dir, 'linter', 'files.zip'))
        result = linter.run()
        self.assertEqual(len(result['warnings']), 1)
        self.assertEqual(result['warnings'][0], 'warning')

    def test_runException(self):
        linter = MyLinter(source_zip_url='#broken')
        result = linter.run()
        self.assertFalse(result['success'])
        self.assertEqual(len(result['warnings']), 1)

    @mock.patch('requests.post')
    def test_callback(self, mock_request_post):
        expected_response_code = 200
        response_string = 'OK'
        self.set_mock_response(mock_request_post, expected_response_code, response_string)
        lint_callback = 'http://dummy.org'
        identity = "my_stuff"
        linter = MyLinter(source_zip_url='#broken', source_dir='source_dir', lint_callback=lint_callback,
                          identity=identity)
        linter.mock_download = True
        result = linter.run()
        self.validate_response(result, linter, expected_response_code, valid_identity=True)

    @mock.patch('requests.post')
    def test_callback_failure(self, mock_request_post):
        expected_response_code = 504
        response_string = 'Timed out'
        self.set_mock_response(mock_request_post, expected_response_code, response_string)
        lint_callback = 'http://dummy.org'
        identity = "my_stuff"
        linter = MyLinter(source_zip_url='#broken', source_dir='source_dir', lint_callback=lint_callback,
                          identity=identity)
        result = linter.run()
        self.validate_response(result, linter, expected_response_code, valid_identity=True)

    #
    # helpers
    #

    def validate_response(self, results, linter, expected_response_code, valid_identity=True):
        self.assertEquals(linter.callback_status, expected_response_code)
        self.assertTrue('results' in linter.callback_results)
        self.assertIsNotNone(linter.callback_results['results'])
        self.assertTrue('identity' in linter.callback_results)
        if valid_identity:
            self.assertIsNotNone(linter.callback_results['identity'])
        self.assertEquals(results, linter.callback_results['results'])

    def set_mock_response(self, mock_request_post, expected_response_code, response_string):
        mock_response = Response()
        mock_response.status_code = expected_response_code
        mock_response.reason = response_string
        mock_request_post.return_value = mock_response
