from __future__ import print_function, unicode_literals
import os
import tempfile
import unittest
from contextlib import closing
from converters.md2html_converter import Md2HtmlConverter
from general_tools.file_utils import remove_tree, unzip


class TestMd2HtmlConverter(unittest.TestCase):

    def setUp(self):
        """
        Runs before each test
        """
        self.out_dir = ''

    def tearDown(self):
        """
        Runs after each test
        """
        # delete temp files
        remove_tree(self.out_dir)

    @classmethod
    def setUpClass(cls):
        """
        Called before tests in this class are run
        """
        pass

    @classmethod
    def tearDownClass(cls):
        """
        Called after tests in this class are run
        """
        pass

    def test_close(self):
        """
        This tests that the temp directories are deleted when the class is closed
        """

        with closing(Md2HtmlConverter('', '', '', '', {})) as tx:
            download_dir = tx.download_dir
            files_dir = tx.files_dir

            # verify the directories are present
            self.assertTrue(os.path.isdir(download_dir))
            self.assertTrue(os.path.isdir(files_dir))

        # now they should have been deleted
        self.assertFalse(os.path.isdir(download_dir))
        self.assertFalse(os.path.isdir(files_dir))

    def test_run(self):
        """
        Runs the converter and verifies the output
        """
        # test with the English OBS
        repo = 'https://git.door43.org/Door43-Catalog/en-obs/archive/master.zip'
        out_zip_file = tempfile.mktemp('.zip')
        print(self.out_dir)
        with closing(Md2HtmlConverter(repo, 'obs', None, out_zip_file)) as tx:
            tx.run()

        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        out_dir = tempfile.mkdtemp(prefix='obs_')
        unzip(out_zip_file, out_dir)
        files_to_verify = []
        for i in range(1, 51):
            files_to_verify.append(str(i).zfill(2) + '.html')
        for file_to_verify in files_to_verify:
            file_name = os.path.join(out_dir, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'OBS HTML file not found: {0}'.format(file_name))

if __name__ == '__main__':
    unittest.main()