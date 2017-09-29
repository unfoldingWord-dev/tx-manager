from __future__ import absolute_import, unicode_literals, print_function
import os

from mock import mock
from requests import Response

from tests.linter_tests.linter_unittest import LinterTestCase
from libraries.linters.linter import Linter


class MyLinter(Linter):
    def __init__(self, source_url=None, source_file=None, source_dir=None, commit_data=None,
                 lint_callback=None, identity=None, **kwargs):
        super(MyLinter, self).__init__(source_url=source_url, source_file=source_file,
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
        linter = MyLinter(source_file=os.path.join(self.resources_dir, 'linter', 'files.zip'))
        results = linter.run()
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0], 'warning')

    def test_runException(self):
        linter = MyLinter(source_url='#broken')
        results = linter.run()
        self.assertFalse(results['success'])
        self.assertEqual(len(results['warnings']), 1)

    @mock.patch('requests.post')
    def test_callback(self, mock_request_post):
        expected_response_code = 200
        response_string = 'OK'
        self.set_mock_response(mock_request_post, expected_response_code, response_string)
        lint_callback = 'http://dummy.org'
        identity = "my_stuff"
        linter = MyLinter(source_url='#broken', source_dir='source_dir', lint_callback=lint_callback,
                          identity=identity)
        linter.mock_download = True
        results = linter.run()
        self.validate_response(results, linter, expected_response_code, valid_identity=True)

    @mock.patch('requests.post')
    def test_callback_failure(self, mock_request_post):
        expected_response_code = 504
        response_string = 'Timed out'
        self.set_mock_response(mock_request_post, expected_response_code, response_string)
        lint_callback = 'http://dummy.org'
        identity = "my_stuff"
        linter = MyLinter(source_url='#broken', source_dir='source_dir', lint_callback=lint_callback,
                          identity=identity)
        results = linter.run()
        self.validate_response(results, linter, expected_response_code, valid_identity=True)

    @mock.patch('requests.post')
    def test_callback_invalid_url(self, mock_request_post):
        expected_response_code = 0
        response_string = 'Timed out'
        self.set_mock_response(mock_request_post, expected_response_code, response_string)
        lint_callback = 'dummy.org'
        identity = "my_stuff"
        linter = MyLinter(source_url='#broken', source_dir='source_dir', lint_callback=lint_callback,
                          identity=identity)
        results = linter.run()
        self.validate_response(results, linter, expected_response_code, valid_identity=True)

    @mock.patch('requests.post')
    def test_callback_missing_identity(self, mock_request_post):
        expected_response_code = 200
        response_string = 'OK'
        self.set_mock_response(mock_request_post, expected_response_code, response_string)
        lint_callback = 'http://dummy.org'
        identity = "my_stuff"
        linter = MyLinter(source_url='#broken', source_dir='source_dir', lint_callback=lint_callback)
        linter.mock_download = True
        results = linter.run()
        self.validate_response(results, linter, expected_response_code, valid_identity=False)

    #
    # helpers
    #

    def validate_response(self, results, linter, expected_response_code, valid_identity=True):
        self.assertEquals(linter.callback_status, expected_response_code)
        self.assertIsNotNone(linter.callback_results)
        self.assertTrue('identity' in linter.callback_results)
        if valid_identity:
            self.assertIsNotNone(linter.callback_results['identity'])
        self.assertEquals(results, linter.callback_results)

    def set_mock_response(self, mock_request_post, expected_response_code, response_string):
        mock_response = Response()
        mock_response.status_code = expected_response_code
        mock_response.reason = response_string
        mock_request_post.return_value = mock_response
