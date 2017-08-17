from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.checkers.ulb_checker import UlbChecker
from libraries.general_tools.file_utils import unzip


class TestUlbChecker(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    converter_resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../converter_tests/resources')

    def setUp(self):
        """Runs before each test."""
        self.preconvert_dir = os.path.join(self.resources_dir, 'some-ulb-dir')  # Change when we have something to test
        self.temp_dir = tempfile.mkdtemp(prefix='temp_ulb_')
        self.converted_dir = os.path.join(self.temp_dir, 'ulb')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_PhpValid(self):
        out_dir = self.unzip_resource('51-PHP.zip')
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

    def unzip_resource(self, zip_name):
        zip_file = os.path.join(self.converter_resources_dir, zip_name)
        out_dir = os.path.join(self.temp_dir, 'checker_test')
        unzip(zip_file, out_dir)
        return out_dir
