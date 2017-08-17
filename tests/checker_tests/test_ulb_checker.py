from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.checkers.ulb_checker import UlbChecker


class TestUlbChecker(unittest.TestCase):

    php_file_name = '51-PHP.usfm'
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.preconvert_dir = os.path.join(self.resources_dir, 'some-ulb-dir')  # Change when we have something to test
        self.temp_dir = tempfile.mkdtemp(prefix='temp_ulb_')
        self.converted_dir = os.path.join(self.temp_dir, 'ulb')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_PhpValid(self):
        out_dir = self.copy_resource(TestUlbChecker.php_file_name)
        expected_warnings = False
        expected_errors = False
        checker = UlbChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    #
    # helpers
    #

    def verify_results(self, expected_errors, expected_warnings, checker):
        self.assertEqual(len(checker.log.logs["warning"]) > 0, expected_warnings)
        self.assertEqual(len(checker.log.logs["error"]) > 0, expected_errors)

    def copy_resource(self, file_name):
        file_path = os.path.join(self.resources_dir, file_name)
        out_dir = os.path.join(self.temp_dir, 'checker_test')
        os.mkdir(out_dir)
        shutil.copy(file_path, out_dir)
        return out_dir
