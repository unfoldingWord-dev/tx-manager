from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import mock
import shutil
from libraries.resource_container.ResourceContainer import RC
from libraries.client.preprocessors import do_preprocess, TnPreprocessor
from libraries.general_tools.file_utils import unzip, read_file


class TestTnPreprocessor(unittest.TestCase):

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

    @unittest.skip("Skip test for time reasons - takes too long for automated tests - leave for standalone testing")
    def test_tn_preprocessor(self):
        # given
        repo_name = 'en_tn'
        file_name = os.path.join('raw_sources', repo_name + '.zip')
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)
        repo_dir = os.path.join(repo_dir)
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        repo_name = 'dummy_repo'

        # when
        results, preproc = do_preprocess(rc, repo_dir, self.out_dir)

        # then
        self.assertTrue(preproc.is_multiple_jobs())
        self.assertEquals(len(preproc.get_book_list()), 66)
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'index.json')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '01-GEN.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '67-REV.md')))
        gen = read_file(os.path.join(self.out_dir, '01-GEN.md'))
        self.assertGreater(len(gen), 1000)
        rev = read_file(os.path.join(self.out_dir, '67-REV.md'))
        self.assertGreater(len(rev), 1000)

    def test_tn_preprocessor_short(self):
        # given
        repo_name = 'en_tn_2books'
        file_name = os.path.join('raw_sources', repo_name + '.zip')
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)
        repo_dir = os.path.join(repo_dir)
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        repo_name = 'dummy_repo'

        # when
        results, preproc = do_preprocess(rc, repo_dir, self.out_dir)

        # then
        self.assertTrue(preproc.is_multiple_jobs())
        self.assertEquals(len(preproc.get_book_list()), 2)
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'index.json')))
        self.assertFalse(os.path.isfile(os.path.join(self.out_dir, '01-GEN.md')))
        self.assertFalse(os.path.isfile(os.path.join(self.out_dir, '67-REV.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '02-EXO.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '03-LEV.md')))
        index_json = read_file(os.path.join(self.out_dir, 'index.json'))
        exo = read_file(os.path.join(self.out_dir, '02-EXO.md'))
        self.assertGreater(len(exo), 1000)
        lev = read_file(os.path.join(self.out_dir, '03-LEV.md'))
        self.assertGreater(len(lev), 1000)

    # IMPORTANT
    # This test may fail as it relies on the commit number for languages to be the same as expected
    # These commit numbers could change daily
    # Thus to ensure that this test behaves correctly, the commit numbers specified as variables should be checked
    # to be correct first.
    @unittest.skip("This test is conditional on outside resources we can't control.")
    def test_url_requests_with_get_links(self):
        rc = RC(os.path.join(self.resources_dir, 'manifests', 'ta'))
        tn = TnPreprocessor(rc, tempfile.gettempdir(), tempfile.gettempdir())

        # TODO: add comment here about these needing to be updated ...
        as_tn_commit_number = "5ec1fb81f6"
        en_tn_commit_number = "ccdb2a707b"
        fr_tn_commit_number = "5f066d1aab"

        content = """
        [link](rc://as/tn/help/rut/04/14)
        [link](rc://en/tn/help/1co/05/14)
        [link](rc://fr/tn/help/1co/06/14)
        [link](rc://fr/tn/help/1co/07/14)
        [link](rc://fr/tn/help/1co/08/14)
        """
        expected = """
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/as_tn/{}/8-RUT.html#tn-chunk-rut-004-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/en_tn/{}/47-1CO.html#tn-chunk-1co-005-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/fr_tn/{}/47-1CO.html#tn-chunk-1co-006-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/fr_tn/{}/47-1CO.html#tn-chunk-1co-007-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/fr_tn/{}/47-1CO.html#tn-chunk-1co-008-014)
        """.format(
            as_tn_commit_number, en_tn_commit_number, fr_tn_commit_number, fr_tn_commit_number, fr_tn_commit_number
        )

        converted = tn.fix_links(content)
        self.assertEqual(expected, converted)

    @mock.patch('requests.get')
    def test_fix_links(self, mock_get):
        mock_get.return_value.url = "http://read.bibletranslationtools.org/u/WA-Catalog/en_tn/ccdb2a707b/"

        # given
        rc = RC(os.path.join(self.resources_dir, 'manifests', 'tn'))
        repo_name = 'Door43'
        current_category = 'names'
        tn = TnPreprocessor(rc, tempfile.gettempdir(), tempfile.gettempdir())
        tn.repo_name = repo_name

        # given
        content = """This link should NOT be converted: [webpage](http://example.com/somewhere/outthere) """
        expected = """This link should NOT be converted: [webpage](http://example.com/somewhere/outthere) """

        # when
        converted = tn.fix_links(content)

        # then
        self.assertEqual(converted, expected)

        # given
        content = """This [link](rc://en/tn/help/ezr/09/01) is a rc link that should go to
            ezr/09/01.md in the en_tn repo"""
        expected = """This [link](http://read.bibletranslationtools.org/u/WA-Catalog/en_tn/ccdb2a707b/15-EZR.html#tn-chunk-ezr-009-001) is a rc link that should go to
            ezr/09/01.md in the en_tn repo"""

        # when
        converted = tn.fix_links(content)

        # then
        self.assertEqual(converted, expected)

        # given
        content = """This url should be made into a link: http://example.com/somewhere/outthere and so should www.example.com/asdf.html?id=5&view=dashboard#report."""
        expected = """This url should be made into a link: [http://example.com/somewhere/outthere](http://example.com/somewhere/outthere) and so should [www.example.com/asdf.html?id=5&view=dashboard#report](http://www.example.com/asdf.html?id=5&view=dashboard#report)."""

        # when
        converted = tn.fix_links(content)

        # then
        self.assertEqual(converted, expected)

        content = """
        [link](rc://en/tn/help/rut/04/14)
        [link](rc://en/tn/help/1co/02/03)
        [link](rc://en/tn/help/1sa/05/12)
        [link](rc://en/tn/help/tit/01/02)
        """
        expected = """
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/en_tn/ccdb2a707b/8-RUT.html#tn-chunk-rut-004-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/en_tn/ccdb2a707b/47-1CO.html#tn-chunk-1co-002-003)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/en_tn/ccdb2a707b/9-1SA.html#tn-chunk-1sa-005-012)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/en_tn/ccdb2a707b/57-TIT.html#tn-chunk-tit-001-002)
        """

        converted = tn.fix_links(content)
        self.assertEqual(expected, converted)

    @classmethod
    def extractFiles(cls, file_name, repo_name):
        file_path = os.path.join(TestTnPreprocessor.resources_dir, file_name)

        # 1) unzip the repo files
        temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = file_path

        # 2) Get the resource container
        rc = RC(repo_dir)

        return rc, repo_dir, temp_dir
