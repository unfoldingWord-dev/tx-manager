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
        unzip(os.path.join(self.resources_dir, 'obs_preconvert', 'en_obs.zip'), self.temp_dir)
        self.preconvert_dir = os.path.join(self.temp_dir, 'en_obs')
        self.expected_warnings = True
        self.expected_errors = False

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_success(self):
        self.expected_warnings = False
        checker = ObsChecker( self.preconvert_dir, None)
        checker.run()
        self.verify_results( self.expected_errors, self.expected_warnings, checker)

    def test_errorMissingChapter(self):
        os.remove(os.path.join(self.preconvert_dir, '25.md'))
        checker = ObsChecker(self.preconvert_dir, None)
        checker.run()
        self.verify_results(self.expected_errors, self.expected_warnings, checker)

    def test_errorMissingFrame(self):
        shutil.copy(os.path.join(self.preconvert_dir, '01-no-frame.md'), os.path.join(self.preconvert_dir, '01.md'))
        checker = ObsChecker(self.preconvert_dir, None)
        checker.run()
        self.verify_results(self.expected_errors, self.expected_warnings, checker)

    def test_errorMissingReference(self):
        shutil.copy(os.path.join(self.preconvert_dir, '01-no-reference.md'), os.path.join(self.preconvert_dir, '01.md'))
        checker = ObsChecker(self.preconvert_dir, None)
        checker.run()
        self.verify_results(self.expected_errors, self.expected_warnings, checker)

    def test_errorMissingTitle(self):
        shutil.copy(os.path.join(self.preconvert_dir, '01-no-title.md'), os.path.join(self.preconvert_dir, '01.md'))
        checker = ObsChecker(self.preconvert_dir, None)
        checker.run()
        self.verify_results(self.expected_errors, self.expected_warnings, checker)

    def test_errorMissingFront(self):
        os.remove(os.path.join(self.preconvert_dir, 'front.md'))
        checker = ObsChecker(self.preconvert_dir, None)
        checker.run()
        self.verify_results(self.expected_errors, self.expected_warnings, checker)

    def test_errorMissingBack(self):
        os.remove(os.path.join(self.preconvert_dir, 'back.md'))
        checker = ObsChecker(self.preconvert_dir, None)
        checker.run()
        self.verify_results(self.expected_errors, self.expected_warnings, checker)

    def test_errorEnglishFront(self):
        shutil.copy(os.path.join(self.preconvert_dir, 'en-front.md'), os.path.join(self.preconvert_dir, 'front.md'))
        checker = ObsChecker(self.preconvert_dir, None)
        checker.run()
        self.verify_results(self.expected_errors, self.expected_warnings, checker)

    def test_errorEnglishBack(self):
        shutil.copy(os.path.join(self.preconvert_dir, 'en-back.md'), os.path.join(self.preconvert_dir, 'back.md'))
        checker = ObsChecker(self.preconvert_dir, None)
        checker.run()
        self.verify_results(self.expected_errors, self.expected_warnings, checker)

    def verify_results(self, expected_errors, expected_warnings, checker):
        self.assertEqual(len(checker.log.logs["warning"]) > 0, expected_warnings)
        #self.assertEqual(len(checker.log.logs["error"]) > 0, expected_errors)
