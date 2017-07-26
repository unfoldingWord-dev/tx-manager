from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.checkers.tw_checker import TwChecker


class TestTwChecker(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.preconvert_dir = os.path.join(self.resources_dir, 'some-tw-dir')  # Change when we have something to test
        self.temp_dir = tempfile.mkdtemp(prefix='temp_tw_')
        self.converted_dir = os.path.join(self.temp_dir, 'tw')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_success(self):
        expected_warnings = False
        expected_errors = False
        checker = TwChecker(self.preconvert_dir, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def verify_results(self, expected_errors, expected_warnings, checker):
        self.assertEqual(len(checker.log.logs["warning"]) > 0, expected_warnings)
        self.assertEqual(len(checker.log.logs["error"]) > 0, expected_errors)
