from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import shutil
from door43_tools.templaters import Templater
from general_tools.file_utils import unzip


class TestTemplater(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.out_dir = ''
        self.temp_dir = ""

    def tearDown(self):
        """Runs after each test."""
        # delete temp files
        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir, ignore_errors=True)
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def testTemplaterBibleTorah(self):
        test_folder_name = "converted_projects/en-ulb-torah.zip"
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        deployer, success = self.doTemplater(test_file_path)
        self.verifyTemplater(success, expect_success, deployer.output_dir)

    def testTemplaterObsComplete(self):
        test_folder_name = "converted_projects/aab_obs_text_obs-complete.zip"
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        deployer, success = self.doTemplater(test_file_path)
        self.verifyTemplater(success, expect_success, deployer.output_dir)

    def testCommitToDoor43Empty(self):
        test_folder_name = os.path.join('converted_projects', 'aae_obs_text_obs-empty.zip')
        expect_success = True
        missing_chapters = range(1, 51)
        test_file_path = self.extractZipFiles(test_folder_name)
        deployer, success = self.doTemplater(test_file_path)
        self.verifyTemplater(success, expect_success, deployer.output_dir, missing_chapters)

    def testCommitToDoor43MissingFirstFrame(self):
        test_folder_name = "converted_projects/aah_obs_text_obs-missing_first_frame.zip"
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        deployer, success = self.doTemplater(test_file_path)
        self.verifyTemplater(success, expect_success, deployer.output_dir)

    def testCommitToDoor43MissingChapter50(self):
        test_folder_name = os.path.join('converted_projects', 'aai_obs_text_obs-missing_chapter_50.zip')
        expect_success = True
        missing_chapters = [50]
        test_file_path = self.extractZipFiles(test_folder_name)
        deployer, success = self.doTemplater(test_file_path)
        self.verifyTemplater(success, expect_success, deployer.output_dir, missing_chapters)

    def extractZipFiles(self, test_folder_name):
        file_path = os.path.join(self.resources_dir, test_folder_name)
        self.temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, self.temp_dir)
        return self.temp_dir

    def doTemplater(self, test_folder_name):
        template_file = os.path.join(self.resources_dir, 'templates', 'obs.html')
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        success = True
        templater = Templater(test_folder_name, self.out_dir, template_file)
        try:
            templater.run()
        except Exception as e:
            print("Templater threw exception: ")
            print(e)
            success = False

        return templater, success

    def verifyTemplater(self, success, expect_success, output_folder, missing_chapters = []):
        self.assertIsNotNone(output_folder)
        self.assertEqual(success, expect_success)

        files_to_verify = []
        files_missing = []
        for i in range(1, 51):
            file_name = str(i).zfill(2) + '.html'
            files_to_verify.append(file_name)

        for file_to_verify in files_to_verify:
            file_name = os.path.join(output_folder, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'file not found: {0}'.format(file_name))

        for file_to_verify in files_missing:
            file_name = os.path.join(output_folder, file_to_verify)
            self.assertFalse(os.path.isfile(file_name), 'file present, but should not be: {0}'.format(file_name))


if __name__ == '__main__':
    unittest.main()
