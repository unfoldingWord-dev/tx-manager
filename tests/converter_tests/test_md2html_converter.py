from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import codecs
from contextlib import closing
from converters.md2html_converter import Md2HtmlConverter
from general_tools.file_utils import remove_tree, unzip, remove
from bs4 import BeautifulSoup


class TestMd2HtmlConverter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    out_zip_file = None

    def setUp(self):
        """Runs before each test."""
        self.out_dir = ''
        self.out_zip_file = ''

    def tearDown(self):
        """Runs after each test."""
        # delete temp files
        remove_tree(self.out_dir)
        remove(self.out_zip_file)

    @classmethod
    def setUpClass(cls):
        """Called before tests in this class are run."""
        pass

    @classmethod
    def tearDownClass(cls):
        """Called after tests in this class are run."""
        pass

    def test_close(self):
        """This tests that the temp directories are deleted when the class is closed."""

        with closing(Md2HtmlConverter('', '', '', '', {})) as tx:
            download_dir = tx.download_dir
            files_dir = tx.files_dir
            out_dir = tx.output_dir

            # verify the directories are present
            self.assertTrue(os.path.isdir(download_dir))
            self.assertTrue(os.path.isdir(files_dir))
            self.assertTrue(os.path.isdir(out_dir))

            # now they should have been deleted
        self.assertFalse(os.path.isdir(download_dir))
        self.assertFalse(os.path.isdir(files_dir))
        self.assertFalse(os.path.isdir(out_dir))

    def test_run(self):
        """Runs the converter and verifies the output."""
        # test with the English OBS
        zip_file = self.resources_dir+"/en-obs.zip"
        out_zip_file = tempfile.mktemp(prefix="en-obs", suffix=".zip")
        with closing(Md2HtmlConverter('', 'obs', None, out_zip_file)) as tx:
            tx.input_zip_file = zip_file
            tx.run()

        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        self.out_dir = tempfile.mkdtemp(prefix='obs_')
        unzip(out_zip_file, self.out_dir)
        remove(out_zip_file)
        files_to_verify = []
        for i in range(1, 51):
            files_to_verify.append(str(i).zfill(2) + '.html')
        for file_to_verify in files_to_verify:
            file_name = os.path.join(self.out_dir, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'OBS HTML file not found: {0}'.format(file_name))

    def test_completeMD(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'en-obs.zip'
        self.expected_warnings = 0
        self.expected_errors = 0
        self.expected_success = True
        self.expected_info_empty = False;

        # when
        tx = self.doTransformObs(file_name)

        #then
        self.verifyTransform(tx)

    def test_BrokenChapter01(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'en-obs-broken_chapter_01.zip'
        self.expected_warnings = 3
        self.expected_errors = 0
        self.expected_success = True
        self.expected_info_empty = False;
        missing_chapters = [1]

        # when
        tx = self.doTransformObs(file_name)

        #then
        self.verifyTransform(tx, missing_chapters)

    def test_MissingFirstChunk(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'en-obs-missing_first_chunk.zip'
        self.expected_warnings = 1
        self.expected_errors = 0
        self.expected_success = True
        self.expected_info_empty = False;
        missing_chapters = []

        # when
        tx = self.doTransformObs(file_name)

        #then
        self.verifyTransform(tx, missing_chapters)

    def test_MissingChapter01(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'en-obs-missing_chapter_01.zip'
        self.expected_warnings = 1
        self.expected_errors = 0
        self.expected_success = True
        self.expected_info_empty = False;
        missing_chapters = [1]

        # when
        tx = self.doTransformObs(file_name)

        #then
        self.verifyTransform(tx, missing_chapters)

    def doTransformObs(self, file_name):
        zip_file_path = os.path.join(self.resources_dir, file_name)
        self.out_zip_file = tempfile.mktemp(prefix="en-obs", suffix=".zip")
        self.return_val = None
        with closing(Md2HtmlConverter('', 'obs', None, self.out_zip_file)) as tx:
            tx.input_zip_file = zip_file_path
            self.return_val = tx.run()
        return tx

    def verifyTransform(self, tx, missing_chapters = []):
        self.assertTrue(os.path.isfile(self.out_zip_file), "There was no output zip file produced.")
        self.assertIsNotNone(self.return_val, "There was no return value.")
        self.out_dir = tempfile.mkdtemp(prefix='obs_')
        unzip(self.out_zip_file, self.out_dir)
        remove(self.out_zip_file)

        files_to_verify = []
        files_missing = []
        for i in range(1, 51):
            file_name = str(i).zfill(2) + '.html'
            if not i in missing_chapters:
                files_to_verify.append(file_name)
            else:
                files_missing.append(file_name)

        for file_to_verify in files_to_verify:
            file_path = os.path.join(self.out_dir, file_to_verify)
            contents = self.getContents(file_path)
            self.assertIsNotNone(contents, 'OBS HTML body contents not found: {0}'.format(os.path.basename(file_path)))

        for file_to_verify in files_missing:
            file_path = os.path.join(self.out_dir, file_to_verify)
            contents = self.getContents(file_path)
            self.assertIsNone(contents, 'OBS HTML body contents present, but should not be: {0}'.format(os.path.basename(file_path)))

        self.assertEqual(self.return_val['success'], self.expected_success, "Mismatch in for success boolean")
        self.assertEqual(len(self.return_val['info']) == 0, self.expected_info_empty, "Mismatch in expected info empty")
        for warning in self.return_val['warnings']:
            print("Warning: " + warning)
        for error in self.return_val['errors']:
            print("Error: " + error)
        self.assertEqual(len(self.return_val['warnings']), self.expected_warnings, "Mismatch in expected warnings")
        self.assertEqual(len(self.return_val['errors']), self.expected_errors, "Mismatch in expected errors")

    def getContents(self, file_path):
        if not os.path.isfile(file_path):
            return None

        soup = None

        with codecs.open(file_path, 'r', 'utf-8-sig') as f:
            soup = BeautifulSoup(f, 'html.parser')

        if not soup:
            return None

        body = soup.find('body')
        if not body:
            return None

        content = body.find(id='content')
        if not content:
            return None

        # make sure we have some text
        text = content.text
        if( (text==None) | (len(text) <= 2)): # length should be longer than a couple of linefeeds
            return None

        return content


if __name__ == '__main__':
    unittest.main()
