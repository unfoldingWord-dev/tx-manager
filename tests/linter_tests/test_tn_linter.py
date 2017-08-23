from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
import mock
from libraries.linters.tn_linter import TnLinter
from libraries.resource_container.ResourceContainer import RC


class TestTnLinter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_tn_')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint(self, mock_invoke_markdown_linter):
        mock_invoke_markdown_linter.return_value = {}  # Don't care about markdown linting here, just specific tn linting
        expected_warnings = False
        linter = TnLinter('bogus_url', rc=RC(repo_name='en_tn'))
        linter.source_zip_file = os.path.join(self.resources_dir, 'tn_linter', 'en_tn.zip')
        linter.run()
        self.verify_results(expected_warnings, linter)

    def verify_results(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings) > 0, expected_warnings)
