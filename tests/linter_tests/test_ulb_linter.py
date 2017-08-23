from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.linters.ulb_linter import UlbLinter
from libraries.resource_container.ResourceContainer import RC
from libraries.general_tools.file_utils import add_contents_to_zip


class TestUlbLinter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    php_repo_path = os.path.join(resources_dir, 'es_php_text_ulb')
    php_file_name = '51-PHP.usfm'
    php_file_path = os.path.join(php_repo_path, php_file_name)

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_ulb_')
        self.rc = RC(self.resources_dir)

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_PhpValid(self):  # for now use same source as for usfm
        out_dir = self.copy_resource(self.php_file_path)
        expected_warnings = False
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    #
    # helpers
    #

    def run_linter(self, out_dir):
        source_zip_file = tempfile.mktemp(prefix='source_zip_file', suffix='.zip', dir=self.temp_dir)
        add_contents_to_zip(source_zip_file, out_dir)
        linter = UlbLinter(source='bogus url', rc=self.rc)
        linter.source_zip_file = source_zip_file
        linter.run()
        return linter

    def verify_results(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings) > 0, expected_warnings)

    def copy_resource(self, file_path):
        out_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix='linter_test')
        shutil.copy(file_path, out_dir)
        return out_dir
