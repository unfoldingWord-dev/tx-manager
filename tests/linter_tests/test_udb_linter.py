from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.linters.udb_linter import UdbLinter
from libraries.resource_container.ResourceContainer import RC


class TestUdbLinter(unittest.TestCase):

    php_file_name = '51-PHP.usfm'
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    testRC = RC(resources_dir)

    def setUp(self):
        """Runs before each test."""
        self.preconvert_dir = os.path.join(self.resources_dir, 'some-udb-dir')  # Change when we have something to test
        self.temp_dir = tempfile.mkdtemp(prefix='temp_udb_')
        self.converted_dir = os.path.join(self.temp_dir, 'udb')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_PhpValid(self):  # for now use same source as for usfm
        out_dir = self.copy_resource(TestUdbLinter.php_file_name)
        expected_warnings = False
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    #
    # helpers
    #

    def run_linter(self, out_dir):
        linter = UdbLinter(out_dir, self.converted_dir)
        linter.rc = TestUdbLinter.testRC
        linter.run()
        return linter

    def verify_results(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings) > 0, expected_warnings)

    def copy_resource(self, file_name):
        file_path = os.path.join(self.resources_dir, file_name)
        out_dir = os.path.join(self.temp_dir, 'linter_test')
        os.mkdir(out_dir)
        shutil.copy(file_path, out_dir)
        return out_dir
