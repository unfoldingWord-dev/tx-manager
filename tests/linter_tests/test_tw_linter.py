from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import shutil
import mock

from libraries.general_tools.file_utils import read_file, write_file, unzip, add_contents_to_zip
from tests.linter_tests.linter_unittest import LinterTestCase
from libraries.linters.tw_linter import TwLinter


class TestTwLinter(LinterTestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_tw_')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint(self, mock_invoke_markdown_linter):
        mock_invoke_markdown_linter.return_value = {}  # Don't care about markdown linting here, just specific tw linting
        expected_warnings = False
        zip_file = os.path.join(self.resources_dir, 'tw_linter', 'en_tw.zip')
        linter = TwLinter(source_zip_file=zip_file)
        linter.run()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint_broken_links(self, mock_invoke_markdown_linter):
        mock_invoke_markdown_linter.return_value = {}  # Don't care about markdown linting here, just specific tw linting
        expected_warnings = True
        zip_file = os.path.join(self.resources_dir, 'tw_linter', 'en_tw.zip')
        new_zip = self.replace_text(zip_file, 'en_tw', 'names.md', '(#moses)', '(../moses.md)')
        linter = TwLinter(source_zip_file=new_zip)
        linter.run()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint_broken_links2(self, mock_invoke_markdown_linter):
        mock_invoke_markdown_linter.return_value = {}  # Don't care about markdown linting here, just specific tw linting
        expected_warnings = True
        zip_file = os.path.join(self.resources_dir, 'tw_linter', 'en_tw.zip')
        new_zip = self.replace_text(zip_file, 'en_tw', 'names.md', '(#moses)', '(./moses.md)')
        linter = TwLinter(source_zip_file=new_zip)
        linter.run()
        self.verify_results(expected_warnings, linter)

    def verify_results(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings) > 0, expected_warnings)

    #
    # helpers
    #

    def replace_text(self, zip_name, sub_folder, file_name, match, replace):
        out_dir = self.unzip_resource(zip_name)
        file_path = os.path.join(out_dir, sub_folder, file_name)
        text = read_file(file_path)
        new_text = text.replace(match, replace)
        write_file(file_path, new_text)

        new_zip = tempfile.mktemp(prefix="linter", suffix='.zip', dir=self.temp_dir)
        add_contents_to_zip(new_zip, out_dir)
        return new_zip

    def unzip_resource(self, zip_name):
        zip_file = os.path.join(self.resources_dir, zip_name)
        out_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix='linter_test_')
        unzip(zip_file, out_dir)
        return out_dir
