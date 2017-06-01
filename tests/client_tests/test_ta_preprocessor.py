from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import shutil
import markdown
from resource_container.ResourceContainer import RC
from client.preprocessors import do_preprocess
from general_tools.file_utils import unzip, read_file
from bs4 import BeautifulSoup


class TestTaPreprocessor(unittest.TestCase):

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

    def test_ta_preprocessor(self):
        file_name = os.path.join('raw_sources', 'en_ta.zip')
        repo_name = 'en_ta'
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        do_preprocess(rc, repo_dir, self.out_dir)
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'checking.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'intro.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'process.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'translate.md')))
        soup = BeautifulSoup(markdown.markdown(read_file(os.path.join(self.out_dir, 'checking.md'))), 'html.parser')
        self.assertEqual(soup.h1.text, "Checking Manual")
        self.assertIsNotNone(soup.find("a", {"name": "accurate"}))
        self.assertEqual(len(soup.find_all('li')), 350)

    @classmethod
    def extractFiles(self, file_name, repo_name):
        file_path = os.path.join(TestTaPreprocessor.resources_dir, file_name)

        # 1) unzip the repo files
        temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = file_path

        # 2) Get the resource container
        rc = RC(repo_dir)

        return rc, repo_dir, temp_dir
