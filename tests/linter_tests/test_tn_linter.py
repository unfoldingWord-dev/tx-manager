from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import shutil
import mock
from tests.linter_tests.linter_unittest import LinterTestCase
from libraries.linters.tn_linter import TnLinter


class TestTnLinter(LinterTestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_tn_')
        self.commit_data = {
            'repository': {
                'name': 'en_tq',
                'owner': {
                    'username': 'door43'
                }
            }
        }

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint(self, mock_invoke_markdown_linter):
        # given
        mock_invoke_markdown_linter.return_value = {}  # Don't care about markdown linting here, just specific tn linting
        expected_warnings = 0
        zip_file = os.path.join(self.resources_dir, 'tn_linter', 'en_tn.zip')
        linter = TnLinter(source_file=zip_file, commit_data=self.commit_data, source_url='http://door43.org/dummy?convert_only=01-GEN.md')
        linter.check_for_exclusive_convert()
        linter.source_zip_url = None  # so we use test zip file

        # when
        linter.run()

        # then
        self.verify_results_warnings_count(expected_warnings, linter)

    #
    # helpers
    #

    def verify_results_warnings_count(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings), expected_warnings)
