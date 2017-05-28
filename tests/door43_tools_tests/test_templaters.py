from __future__ import absolute_import, unicode_literals, print_function
import codecs
import os
import tempfile
import unittest
import shutil
from bs4 import BeautifulSoup
from door43_tools.templaters import do_template
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

    def testTemplaterBibleFourBooks(self):
        test_folder_name = "converted_projects/en-ulb-4-books.zip"
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('bible', test_file_path)
        self.verifyBibleTemplater(success, expect_success, self.out_dir,
                                  ['01-GEN.html', '02-EXO.html', '03-LEV.html', '05-DEU.html'])

    def testTemplaterObsComplete(self):
        test_folder_name = "converted_projects/aab_obs_text_obs-complete.zip"
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('obs', test_file_path)
        self.verifyObsTemplater(success, expect_success, self.out_dir)

    def testCommitToDoor43Empty(self):
        test_folder_name = os.path.join('converted_projects', 'aae_obs_text_obs-empty.zip')
        expect_success = True
        missing_chapters = range(1, 51)
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('obs', test_file_path)
        self.verifyObsTemplater(success, expect_success, self.out_dir, missing_chapters)

    def testCommitToDoor43MissingFirstFrame(self):
        test_folder_name = "converted_projects/aah_obs_text_obs-missing_first_frame.zip"
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('obs', test_file_path)
        self.verifyObsTemplater(success, expect_success, self.out_dir)

    def testCommitToDoor43MissingChapter50(self):
        test_folder_name = os.path.join('converted_projects', 'aai_obs_text_obs-missing_chapter_50.zip')
        expect_success = True
        missing_chapters = [50]
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('obs', test_file_path)
        self.verifyObsTemplater(success, expect_success, self.out_dir, missing_chapters)

    def testTemplaterRightToLeft(self):
        test_folder_name = os.path.join('converted_projects', 'glk_obs_text_obs-complete.zip')
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('obs', test_file_path)

        # check for dir attribute in html tag
        with codecs.open(os.path.join(self.out_dir, '01.html'), 'r', 'utf-8-sig') as f:
            soup = BeautifulSoup(f, 'html.parser')

        self.assertIn('dir', soup.html.attrs)
        self.assertEqual('rtl', soup.html.attrs['dir'])

    def extractZipFiles(self, test_folder_name):
        file_path = os.path.join(self.resources_dir, test_folder_name)
        self.temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, self.temp_dir)
        return self.temp_dir

    def doTemplater(self, resource_type, test_folder_name):
        template_file = os.path.join(self.resources_dir, 'templates', '{0}.html'.format(resource_type))
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        try:
            return do_template(resource_type,test_folder_name, self.out_dir, template_file)
        except Exception as e:
            print("do_template threw exception: ")
            print(e)
            return False

    def verifyObsTemplater(self, success, expect_success, output_folder, missing_chapters = []):
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

    def verifyBibleTemplater(self, success, expect_success, output_folder, files_to_verify):
        self.assertIsNotNone(output_folder)
        self.assertEqual(success, expect_success)
        for file_to_verify in files_to_verify:
            file_name = os.path.join(output_folder, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'file not found: {0}'.format(file_name))

if __name__ == '__main__':
    unittest.main()
