from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import shutil
from tests.linter_tests.linter_unittest import LinterTestCase
from libraries.linters.ulb_linter import UlbLinter


class TestUlbLinter(LinterTestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    php_repo_path = os.path.join(resources_dir, 'es_php_text_ulb')
    php_file_name = '51-PHP.usfm'
    php_file_path = os.path.join(php_repo_path, php_file_name)

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='tmp_ulb_')

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
        linter = UlbLinter(source_dir=out_dir)
        linter.run()
        return linter

    def verify_results(self, expected_warnings, linter):
        self.assertEqual(len(linter.log.warnings) > 0, expected_warnings)

    def copy_resource(self, file_path):
        out_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix='linter_test')
        shutil.copy(file_path, out_dir)
        return out_dir
