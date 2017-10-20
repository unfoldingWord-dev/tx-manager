from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import shutil
import mock
from libraries.client.preprocessors import TqPreprocessor
from libraries.general_tools import file_utils
from libraries.general_tools.file_utils import unzip, write_file, read_file, add_contents_to_zip
from libraries.door43_tools.bible_books import BOOK_NUMBERS
from tests.linter_tests.linter_unittest import LinterTestCase
from libraries.linters.tq_linter import TqLinter


class TestTqLinter(LinterTestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_tq_')
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
        mock_invoke_markdown_linter.return_value = {}  # Don't care about markdown linting here, just specific tq linting
        expected_warnings = 0 
        zip_file = os.path.join(self.resources_dir, 'tq_linter', 'en_tq.zip')
        linter = TqLinter(source_file=zip_file, commit_data=self.commit_data)

        # when
        linter.run()

        # then
        self.verify_results_warnings_count(expected_warnings, linter)

    @mock.patch('libraries.linters.markdown_linter.MarkdownLinter.invoke_markdown_linter')
    def test_lint_broken_links(self, mock_invoke_markdown_linter):
        # given
        mock_invoke_markdown_linter.return_value = {}  # Don't care about markdown linting here, just specific tw linting
        expected_warnings = 66-2  # we only leave 2 books
        zip_file = os.path.join(self.resources_dir, 'tq_linter', 'en_tq.zip')
        out_dir = self.unzip_resource(zip_file)

        # remove everything past genesis
        for book in BOOK_NUMBERS: 
            link = self.get_link_for_book('{0}-{1}.html'.format(BOOK_NUMBERS[book], book.upper()))
            book_path = os.path.join(out_dir, 'en_tq', link)
            if os.path.exists(book_path):
                if BOOK_NUMBERS[book] > "02":
                    file_utils.remove_tree(book_path)

        # put a verse in exo so that we can test that there is some content there
        file_path = os.path.join(out_dir, 'en_tq/exo/01/05.md')
        file_utils.write_file(file_path, 'dummy')

        # create chapter in lev with no md files so that we can test that there is no content there
        file_path = os.path.join(os.path.join(out_dir, 'en_tq/lev/01/readme.txt'))
        file_utils.write_file(file_path, 'dummy')

        new_zip = self.create_new_zip(out_dir)
        linter = TqLinter(source_file=new_zip, commit_data=self.commit_data)

        # when
        linter.run()

        # then
        self.verify_results_warnings_count(expected_warnings, linter)

    #
    # helpers
    #

    def verify_results_warnings_count(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings), expected_warnings)

    def verify_results_warnings_count(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings), expected_warnings)

    def replace_text(self, out_dir, file_name, match, replace):
        file_path = os.path.join(out_dir, file_name)
        text = read_file(file_path)
        new_text = text.replace(match, replace)
        self.assertNotEqual(text, new_text)
        write_file(file_path, new_text)

    def create_new_zip(self, out_dir):
        new_zip = tempfile.mktemp(prefix="linter", suffix='.zip', dir=self.temp_dir)
        add_contents_to_zip(new_zip, out_dir)
        return new_zip

    def prepend_text(self, out_dir, file_name, prefix):
        file_path = os.path.join(out_dir, file_name)
        text = read_file(file_path)
        new_text = prefix + text
        write_file(file_path, new_text)

    def unzip_resource(self, zip_name):
        zip_file = os.path.join(self.resources_dir, zip_name)
        out_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix='linter_test_')
        unzip(zip_file, out_dir)
        return out_dir

    def get_link_for_book(self, book):
        parts = book.split('-')
        link = book
        if len(parts) > 1:
            link = parts[1].lower()
        return link
