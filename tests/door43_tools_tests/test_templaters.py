from __future__ import absolute_import, unicode_literals, print_function
import codecs
import os
import tempfile
import unittest
import shutil
import re
from bs4 import BeautifulSoup
from libraries.door43_tools.templaters import do_template, init_template
from libraries.general_tools.file_utils import unzip, read_file


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
        test_folder_name = os.path.join('converted_projects', 'en-ulb-4-books.zip')
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('bible', test_file_path)
        self.verifyBibleTemplater(success, expect_success, self.out_dir,
                                  ['01-GEN.html', '02-EXO.html', '03-LEV.html', '05-DEU.html'])

    def testTemplaterObsComplete(self):
        test_folder_name = os.path.join('converted_projects', 'aab_obs_text_obs-complete.zip')
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('obs', test_file_path)
        self.verifyObsTemplater(success, expect_success, self.out_dir)

    def testTemplaterTaComplete(self):
        test_folder_name = os.path.join('converted_projects', 'en_ta-complete.zip')
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        success = self.doTemplater('ta', test_file_path)
        self.verifyTaTemplater(success, expect_success, self.out_dir,
                               ['checking.html', 'intro.html', 'process.html', 'translate.html'])
        # Verify sidebar nav generated
        soup = BeautifulSoup(read_file(os.path.join(self.out_dir, 'checking.html')), 'html.parser')
        self.assertEqual(len(soup.find('nav', {'id': 'right-sidebar-nav'}).findAll('li')), 49)
        self.assertEqual(len(soup.find('div', {'id': 'content'}).findAll(re.compile(r'h\d+'),
                                                                         {'class': 'section-header'})), 44)

    def testTemplaterTwComplete(self):
        test_folder_name = os.path.join('converted_projects', 'en_tw_converted.zip')
        expect_success = True
        test_file_path = self.extractZipFiles(test_folder_name)
        test_file_path = os.path.join(test_file_path, 'en_tw_converted')
        success = self.doTemplater('tw', test_file_path)
        self.verifyTaTemplater(success, expect_success, self.out_dir, ['kt.html', 'names.html', 'other.html'])
        # Verify sidebar nav generated
        soup = BeautifulSoup(read_file(os.path.join(self.out_dir, 'kt.html')), 'html.parser')
        self.assertEqual(len(soup.find('nav', {'id': 'right-sidebar-nav'}).findAll('li')), 1020)
        self.assertEqual(len(soup.find('div', {'id': 'content'}).findAll(re.compile(r'h\d+'),
                                                                         {'class': 'section-header'})), 212)

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
        test_folder_name = os.path.join(self.resources_dir, 'converted_projects', 'glk_obs_text_obs-complete.zip')
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

    def doTemplater(self, resource_type, test_folder_name, alreadyProcessed=False):
        template_file = os.path.join(self.resources_dir, 'templates', 'project-page.html')
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        if not alreadyProcessed:
            return do_template(resource_type, test_folder_name, self.out_dir, template_file)

        # we pre-process to get title and chapter info
        template_pre = init_template(resource_type, test_folder_name, self.out_dir, template_file)
        template_pre.run()

        # copy pre-processed data and run again
        template = init_template(resource_type, self.out_dir, self.out_dir, template_file)
        template.already_converted = template.files
        template.book_codes = template_pre.book_codes
        template.chapters = template_pre.chapters
        template.titles = template_pre.titles
        return template.run()

    def verifyObsTemplater(self, success, expect_success, output_folder, missing_chapters=[]):
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

    def verifyTaTemplater(self, success, expect_success, output_folder, filesToVerify=[]):
        self.assertIsNotNone(output_folder)
        self.assertEqual(success, expect_success)
        for file_name in filesToVerify:
            self.assertTrue(os.path.isfile(os.path.join(output_folder, file_name)), 'file not found: {0}'
                            .format(file_name))

if __name__ == '__main__':
    unittest.main()
