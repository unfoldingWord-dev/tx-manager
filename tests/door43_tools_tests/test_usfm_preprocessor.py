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

    @classmethod
    def extractObsFiles(self, file_name, repo_name):
        file_path = os.path.join(TestUsfmPreprocessor.resources_dir, file_name)

        # 1) unzip the repo files
        temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = file_path

        # 2) Get the manifest file or make one if it doesn't exist based on meta.json, repo_name and file extensions
        manifest_path = os.path.join(repo_dir, 'manifest.json')
        if not os.path.isfile(manifest_path):
            manifest_path = os.path.join(repo_dir, 'project.json')
            if not os.path.isfile(manifest_path):
                manifest_path = None
        meta_path = os.path.join(repo_dir, 'meta.json')
        meta = None
        if os.path.isfile(meta_path):
            meta = MetaData(meta_path)
        manifest = Manifest(file_name=manifest_path, repo_name=repo_name, files_path=repo_dir, meta=meta)
        return manifest, repo_dir, temp_dir

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




