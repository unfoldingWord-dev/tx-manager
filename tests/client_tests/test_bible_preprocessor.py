from __future__ import absolute_import, unicode_literals, print_function
import codecs
import os
import tempfile
import unittest
import shutil
from resource_container.ResourceContainer import RC
from client.preprocessors import do_preprocess
from general_tools.file_utils import unzip


class TestBiblePreprocessor(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """
        Runs before each test
        """
        self.out_dir = ''
        self.temp_dir = ""

    def tearDown(self):
        """
        Runs after each test
        """
        # delete temp files
        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir, ignore_errors=True)
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_BiblePreprocessorComplete(self):

        #given
        file_name = os.path.join('raw_sources', 'aa_php_text_ulb.zip')
        repo_name = 'aa_php_text_ulb'
        expectedOutput = '51-PHP.usfm'
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)

        # when
        folder = self.runBiblePreprocessor(rc, repo_dir)

        #then
        self.verifyTransform(folder, expectedOutput)

    @classmethod
    def extractFiles(self, file_name, repo_name):
        file_path = os.path.join(TestBiblePreprocessor.resources_dir, file_name)

        # 1) unzip the repo files
        temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = file_path

        # 2) Get the resource container
        rc = RC(repo_dir)
        return rc, repo_dir, temp_dir

    def runBiblePreprocessor(self, rc, repo_dir):
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        do_preprocess(rc, repo_dir, self.out_dir)
        return self.out_dir

    def verifyTransform(self, folder, expectedName):
        file_name = os.path.join(folder, expectedName)
        self.assertTrue(os.path.isfile(file_name), 'Bible usfm file not found: {0}'.format(expectedName))

        usfm = None
        with codecs.open(file_name, 'r', 'utf-8-sig') as usfm_file:
            usfm = usfm_file.read()

        self.assertIsNotNone(usfm);
        self.assertTrue(len(usfm) > 10, 'Bible usfm file contents missing: {0}'.format(expectedName))




