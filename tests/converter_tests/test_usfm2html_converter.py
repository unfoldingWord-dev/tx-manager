from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
from contextlib import closing
from converters.usfm2html_converter import Usfm2HtmlConverter
from general_tools.file_utils import remove_tree, unzip, remove


class TestUsfmHtmlConverter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

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

        with closing(Usfm2HtmlConverter('', '', '', '', {})) as tx:
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
        """
        Runs the converter and verifies the output
        """
        # test with the English OBS
        zip_file = self.resources_dir+"/eight_bible_books.zip"
        out_zip_file = tempfile.mktemp('.zip')
        with closing(Usfm2HtmlConverter('', 'udb', None, out_zip_file)) as tx:
            tx.input_zip_file = zip_file
            tx.run()
        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        self.out_dir = tempfile.mkdtemp(prefix='udb_')
        unzip(out_zip_file, self.out_dir)
        remove(out_zip_file)
        files_to_verify = ['60-JAS.html', '61-1PE.html', '62-2PE.html', '63-1JN.html', '64-2JN.html', '65-3JN.html',
                           '66-JUD.html', '67-REV.html']
        for file_to_verify in files_to_verify:
            file_name = os.path.join(self.out_dir, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'UDB HTML file not found: {0}'.format(file_name))

if __name__ == '__main__':
    unittest.main()
