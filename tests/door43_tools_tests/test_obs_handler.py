from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
from door43_tools.obs_handler import OBSInspection


class TestObsHandler(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def test_success(self):

        # given
        expected_warnings = False
        expected_errors = False
        file_name = 'obs_chapters/hu_obs_text_obs/01.html'

        # when
        inspection = self.inspectFile(file_name)

        #then
        self.verify_results(expected_errors, expected_warnings, inspection)

    def test_errorInvalidChapterType(self): # should be ignored

        # given
        expected_warnings = False
        expected_errors = False
        file_name = 'obs_chapters/hu_obs_text_obs/header.html'

        # when
        inspection = self.inspectFile(file_name)

        #then
        self.verify_results(expected_errors, expected_warnings, inspection)

    def test_errorInvalidChapter(self):

        # given
        expected_warnings = True
        expected_errors = False
        file_name = 'obs_chapters/hu_obs_text_obs/9999.html'

        # when
        inspection = self.inspectFile(file_name)

        #then
        self.verify_results(expected_errors, expected_warnings, inspection)

    def test_errorMissingBody(self):

        # given
        expected_warnings = True
        expected_errors = False
        file_name = 'obs_chapters/hu_obs_text_obs/01-no-body.html'
        chapter = 1

        # when
        inspection = self.inspectFile(file_name, chapter)

        #then
        self.verify_results(expected_errors, expected_warnings, inspection)

    def test_invalidMissingContent(self):

        # given
        expected_warnings = True
        expected_errors = False
        file_name = 'obs_chapters/hu_obs_text_obs/01-no-content.html'
        chapter = 1

        # when
        inspection = self.inspectFile(file_name, chapter)

        #then
        self.verify_results(expected_errors, expected_warnings, inspection)

    def test_invalidMissingTitle(self):

        # given
        expected_warnings = True
        expected_errors = False
        file_name = 'obs_chapters/hu_obs_text_obs/01-no-title.html'
        chapter = 1

        # when
        inspection = self.inspectFile(file_name, chapter)

        #then
        self.verify_results(expected_errors, expected_warnings, inspection)

    def test_invalidMissingChunk(self):

        # given
        expected_warnings = True
        expected_errors = False
        file_name = 'obs_chapters/hu_obs_text_obs/01-missing-chunk.html'
        chapter = 1

        # when
        inspection = self.inspectFile(file_name, chapter)

        #then
        self.verify_results(expected_errors, expected_warnings, inspection)

    def test_invalidMissingReference(self):

        # given
        expected_warnings = True
        expected_errors = False
        file_name = 'obs_chapters/hu_obs_text_obs/01-missing-reference.html'
        chapter = 1

        # when
        inspection = self.inspectFile(file_name, chapter)

        #then
        self.verify_results(expected_errors, expected_warnings, inspection)

    def inspectFile(self, file_name, chapter=None):
        file_path = os.path.join(TestObsHandler.resources_dir, file_name)
        inspection = OBSInspection(file_path, chapter)
        inspection.run()
        return inspection

    def verify_results(self, expected_errors, expected_warnings, inspection):
        self.assertEqual(len(inspection.logger.logs["warning"]) > 0, expected_warnings)
        self.assertEqual(len(inspection.logger.logs["error"]) > 0, expected_errors)
