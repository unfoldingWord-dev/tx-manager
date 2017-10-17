from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import shutil
from libraries.resource_container.ResourceContainer import RC
from libraries.client.preprocessors import do_preprocess, TqPreprocessor
from libraries.general_tools.file_utils import unzip, read_file


class TestTqPreprocessor(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.out_dir = ''
        self.temp_dir = ""
        self.save_sections = TqPreprocessor.sections

    def tearDown(self):
        """Runs after each test."""
        TqPreprocessor.sections = self.save_sections
        # delete temp files
        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir, ignore_errors=True)
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_tq_preprocessor(self):
        # given
        repo_name = 'en_tq'
        file_name = os.path.join('raw_sources', repo_name + '.zip')
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)
        repo_dir = os.path.join(repo_dir)
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        repo_name = 'dummy_repo'

        # when
        results, preproc = do_preprocess(rc, repo_dir, self.out_dir)

        # then
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'index.json')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '00-toc.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '01-GEN.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '67-REV.md')))
        toc = read_file(os.path.join(self.out_dir, '00-toc.md'))
        index = read_file(os.path.join(self.out_dir, 'index.json'))
        gen = read_file(os.path.join(self.out_dir, '01-GEN.md'))

    def test_tq_preprocessor_dummy_section(self):
        # given
        TqPreprocessor.sections = [{'book': "dummy", 'title': 'dummy'}]
        repo_name = 'en_tq'
        file_name = os.path.join('raw_sources', 'en_tq_two_books.zip')
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)
        repo_dir = os.path.join(repo_dir)
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        repo_name = 'dummy_repo'

        # when
        results, preproc = do_preprocess(rc, repo_dir, self.out_dir)

        # then
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '00-toc.md')))

    #
    # helpers
    #
    
    @classmethod
    def extractFiles(cls, file_name, repo_name):
        file_path = os.path.join(TestTqPreprocessor.resources_dir, file_name)

        # 1) unzip the repo files
        temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = file_path

        # 2) Get the resource container
        rc = RC(repo_dir)

        return rc, repo_dir, temp_dir
