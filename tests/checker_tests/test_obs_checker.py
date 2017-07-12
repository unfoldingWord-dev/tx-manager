from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.checkers.obs_checker import ObsChecker
from libraries.general_tools.file_utils import unzip


class TestObsChecker(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_obs_')
        unzip(os.path.join(self.resources_dir, 'obs_converted', 'hu_obs_text_obs.zip'), self.temp_dir)
        self.converted_dir = os.path.join(self.temp_dir, 'hu_obs_text_obs')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_success(self):
        expected_warnings = False
        expected_errors = False
        checker = ObsChecker(None, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def test_errorMissingBody(self):
        expected_warnings = True
        expected_errors = False
        shutil.copy(os.path.join(self.converted_dir, '01-no-body.html'), os.path.join(self.converted_dir, '01.html'))
        checker = ObsChecker(None, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def test_invalidMissingContent(self):
        expected_warnings = True
        expected_errors = False
        shutil.copy(os.path.join(self.converted_dir, '01-no-content.html'), os.path.join(self.converted_dir, '01.html'))
        checker = ObsChecker(None, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def test_invalidMissingTitle(self):
        expected_warnings = True
        expected_errors = False
        shutil.copy(os.path.join(self.converted_dir, '01-no-title.html'), os.path.join(self.converted_dir, '01.html'))
        checker = ObsChecker(None, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def test_invalidMissingChunk(self):
        expected_warnings = True
        expected_errors = False
        shutil.copy(os.path.join(self.converted_dir, '01-missing-chunk.html'), os.path.join(self.converted_dir, '01.html'))
        checker = ObsChecker(None, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def test_invalidMissingReference(self):
        expected_warnings = True
        expected_errors = False
        shutil.copy(os.path.join(self.converted_dir, '01-missing-reference.html'), os.path.join(self.converted_dir, '01.html'))
        checker = ObsChecker(None, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def verify_results(self, expected_errors, expected_warnings, checker):
        self.assertEqual(len(checker.log.logs["warning"]) > 0, expected_warnings)
        self.assertEqual(len(checker.log.logs["error"]) > 0, expected_errors)
