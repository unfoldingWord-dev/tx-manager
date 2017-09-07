from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import shutil
import mock
from tests.linter_tests.linter_unittest import LinterTestCase
from libraries.general_tools.file_utils import unzip
from libraries.linters.obs_linter import ObsLinter


class TestObsLinter(LinterTestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    obs_zip_file = os.path.join(resources_dir, 'obs_linter', 'es_obs.zip')
    changed_files_dir = os.path.join(resources_dir, 'obs_linter', 'changed_files')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='tmp_obs_')
        unzip(self.obs_zip_file, self.temp_dir)
        self.repo_dir = os.path.join(self.temp_dir, 'es_obs')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint_no_warnings(self, mock_invoke):
        unzip(self.obs_zip_file, self.temp_dir)
        mock_invoke.return_value = {}
        expected_warnings = False
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint_warnings(self, mock_invoke):
        obs_zip_file = os.path.join(self.resources_dir, 'obs_linter', 'en-obs.zip')
        unzip(obs_zip_file, self.temp_dir)
        source_dir = os.path.join(self.temp_dir, 'en-obs')
        mock_invoke.return_value = {}
        expected_warnings = True
        linter = ObsLinter(source_dir=source_dir)
        linter.run()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingChapter(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        os.remove(os.path.join(self.repo_dir, 'content', '25.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingFrame(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.changed_files_dir, '01-no-frame.md'), os.path.join(self.repo_dir, 'content', '01.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingReference(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.changed_files_dir, '01-no-reference.md'), os.path.join(self.repo_dir, 'content', '01.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingTitle(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.changed_files_dir, '01-no-title.md'), os.path.join(self.repo_dir, 'content', '01.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingFront(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        os.remove(os.path.join(self.repo_dir, 'content', 'front', 'intro.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorMissingBack(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        os.remove(os.path.join(self.repo_dir, 'content', 'back', 'intro.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorEnglishFront(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.changed_files_dir, 'en-front.md'), os.path.join(self.repo_dir, 'content', 'front', 'intro.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_errorEnglishBack(self, mock_invoke):
        mock_invoke.return_value = {}
        expected_warnings = True
        shutil.copy(os.path.join(self.changed_files_dir, 'en-back.md'), os.path.join(self.repo_dir, 'content', 'back', 'intro.md'))
        linter = self.run_linter()
        self.verify_results(expected_warnings, linter)

    def run_linter(self):
        linter = ObsLinter(source_dir=self.repo_dir)
        linter.run()
        return linter

    def verify_results(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings) > 0, expected_warnings)
