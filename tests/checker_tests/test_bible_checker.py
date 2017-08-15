from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.checkers.bible_checker import BibleChecker
from libraries.general_tools.file_utils import unzip, write_file, read_file


class TestBibleChecker(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    converter_resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../converter_tests/resources')

    def setUp(self):
        """Runs before each test."""
        self.preconvert_dir = os.path.join(self.resources_dir, 'some-bible-dir')  # Change when we have something to test
        self.temp_dir = tempfile.mkdtemp(prefix='temp_bible_')
        self.converted_dir = os.path.join(self.temp_dir, 'bible')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_success(self):
        expected_warnings = False
        expected_errors = False
        checker = BibleChecker(self.preconvert_dir, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def test_PhpMissingV1(self):
        out_dir = self.unzip_resource('51-PHP.zip')

        # remove v1
        book_path = os.path.join(out_dir, '51-PHP.usfm')
        book_text = read_file(book_path)
        v1 = book_text.index('\\v 1 ')
        v2 = book_text.index('\\v 2 ')
        new_text = book_text[:v1] + book_text[v2:]
        write_file(book_path, new_text)

        expected_warnings = 1
        expected_errors = 0
        checker = BibleChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    #
    # helpers
    #

    def unzip_resource(self, zip_name):
        zip_file = os.path.join(self.converter_resources_dir, zip_name)
        out_dir = os.path.join(self.temp_dir, 'checker_test')
        unzip(zip_file, out_dir)
        return out_dir

    def verify_results(self, expected_errors, expected_warnings, checker):
        self.assertEqual(len(checker.log.logs["warning"]) > 0, expected_warnings)
        self.assertEqual(len(checker.log.logs["error"]) > 0, expected_errors)

    def verify_results_counts(self, expected_errors, expected_warnings, checker):
        self.assertEqual(len(checker.log.logs["warning"]), expected_warnings)
        self.assertEqual(len(checker.log.logs["error"]), expected_errors)
