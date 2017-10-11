from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.lint_handler import LintHandler
from libraries.linters.markdown_linter import MarkdownLinter


class TestLintHandler(TestCase):

    @mock.patch('libraries.linters.linter.Linter.run')
    def test_handle_for_obs(self, mock_convert_run):
        mock_convert_run.return_value = None
        event = {
            'data': {
                'source_url': 'https://cdn.example.com/preconvert/705948ab00.zip',
                'cdn_bucket': 'test_cdn_bucket',
                'cdn_file': 'tx/job/1234567890.zip',
                'callback': 'https://api.example.com/client/callback',
                'identifier': 'richmahn/en-obs/705948ab00',
                'resource_type': 'obs',
                'options': {'pageSize': 'A4'}
            }
        }
        self.assertIsNone(LintHandler(MarkdownLinter).handle(event, None))
