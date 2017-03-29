from __future__ import absolute_import, unicode_literals, print_function

import codecs

import os
import tempfile
import unittest

import shutil

from door43_tools.manifest_handler import MetaData, Manifest
from door43_tools.preprocessors import TsBibleUsfmPreprocessor
from general_tools.file_utils import unzip, add_contents_to_zip


class TestUsfmPreprocessor(unittest.TestCase):

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

    def test_TsUsfmMarkdownPreprocessorComplete(self):

        #given
        file_name = 'raw_sources/aa_php_text_ulb.zip'
        repo_name = 'aa_php_text_ulb'
        expectedOutput = '51-PHP.usfm'
        manifest, repo_dir, self.temp_dir = self.extractObsFiles(file_name, repo_name)

        # when
        folder = self.runTsUsfmMarkdownPreprocessor(manifest, repo_dir)

        #then
        self.verifyTransform(folder, expectedOutput)

    def runTsUsfmMarkdownPreprocessor(self, manifest, repo_dir):
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        compiler = TsBibleUsfmPreprocessor(manifest, repo_dir, self.out_dir)
        compiler.run()
        return self.out_dir

    def verifyTransform(self, folder, expectedName):
        file_name = os.path.join(folder, expectedName)
        self.assertTrue(os.path.isfile(file_name), 'Bible usfm file not found: {0}'.format(expectedName))

        usfm = None
        with codecs.open(file_name, 'r', 'utf-8-sig') as usfm_file:
            usfm = usfm_file.read()

        self.assertIsNotNone(usfm);
        self.assertTrue(len(usfm) > 10, 'Bible usfm file contents missing: {0}'.format(expectedName))




