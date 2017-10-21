from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import shutil
import markdown2
from libraries.resource_container.ResourceContainer import RC
from libraries.client.preprocessors import do_preprocess, TwPreprocessor
from libraries.general_tools.file_utils import unzip, read_file
from bs4 import BeautifulSoup


class TestTwPreprocessor(unittest.TestCase):

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

    def test_tw_preprocessor(self):
        # given
        repo_name = 'en_tw'
        file_name = os.path.join('raw_sources', repo_name + '.zip')
        rc, repo_dir, self.temp_dir = self.extractFiles(file_name, repo_name)
        repo_dir = os.path.join(repo_dir)
        self.out_dir = tempfile.mkdtemp(prefix='output_')

        # when
        results, preproc = do_preprocess(rc, repo_dir, self.out_dir)

        # then
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'index.json')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'kt.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'names.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'other.md')))
        kt = read_file(os.path.join(self.out_dir, 'kt.md'))
        names = read_file(os.path.join(self.out_dir, 'names.md'))
        other = read_file(os.path.join(self.out_dir, 'other.md'))
        soup = BeautifulSoup(markdown2.markdown(kt, extras=['markdown-in-html', 'tables']), 'html.parser')
        self.assertEqual(soup.h1.text, 'Key Terms')
        self.assertEqual(soup.h2.text, 'abomination, abominations, abominable')
        self.assertIsNotNone(soup.find('a', {'id': 'tw-term-kt-adoption'}))
        self.assertEqual(len(soup.find_all('li')), 4009)
        # Test links have been converted
        # self.assertIsNotNone(soup.find("a", {"href": "#accuracy-check"}))
        # self.assertIsNotNone(soup.find("a", {"href": "03-translate.html#figs-explicit"}))
        # make sure no old links exist
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, 'manifest.yaml')))
        self.assertTrue('(rc:' not in kt)
        self.assertTrue('(rc:' not in names)
        self.assertTrue('(rc:' not in other)
        self.assertTrue('../' not in kt)
        self.assertTrue('../' not in names)
        self.assertTrue('../' not in other)

    def test_fix_links(self):
        # given
        rc = RC(os.path.join(self.resources_dir, 'manifests', 'tw'))
        repo_name = 'Door43'
        current_category = 'names'
        tw = TwPreprocessor(rc, tempfile.gettempdir(), tempfile.gettempdir())
        tw.repo_name = repo_name
        content = "This has links to the same category: (See also: [titus](../names/titus.md), [timothy](../names/timothy.md)"
        expected = "This has links to the same category: (See also: [titus](#titus), [timothy](#timothy)"

        # when
        converted = tw.fix_links(content, current_category)

        # then
        self.assertEqual(converted, expected)

        # given
        content = """This has links to other categories:
        (See also:[lamb](../kt/lamb.md), [license](../other/license.md)"""
        expected = """This has links to other categories:
        (See also:[lamb](kt.html#lamb), [license](other.html#license)"""

        # when
        converted = tw.fix_links(content, current_category)

        # then
        self.assertEqual(converted, expected)

        # given
        content = """This has links to the same category and others:
        (See also: [titus](../names/titus.md), [timothy](../names/timothy.md), [lamb](../kt/lamb.md), 
        [license](../other/license.md)"""
        expected = """This has links to the same category and others:
        (See also: [titus](#titus), [timothy](#timothy), [lamb](kt.html#lamb), 
        [license](other.html#license)"""

        # when
        converted = tw.fix_links(content, current_category)

        # then
        self.assertEqual(converted, expected)

        # given
        content = """This link should NOT be converted: [webpage](http://example.com/somewhere/outthere) """
        expected = """This link should NOT be converted: [webpage](http://example.com/somewhere/outthere) """

        # when
        converted = tw.fix_links(content, current_category)

        # then
        self.assertEqual(converted, expected)

        # given
        content = """This [link](rc://en/tn/help/ezr/09/01) is a rc link that should go to 
            ezr/09/01.md in the en_tn repo"""
        expected = """This [link](https://git.door43.org/Door43/en_tn/src/master/ezr/09/01.md) is a rc link that should go to 
            ezr/09/01.md in the en_tn repo"""

        # when
        converted = tw.fix_links(content, current_category)

        # then
        self.assertEqual(converted, expected)

        # given
        content = """This url should be made into a link: http://example.com/somewhere/outthere and so should www.example.com/asdf.html?id=5&view=dashboard#report."""
        expected = """This url should be made into a link: [http://example.com/somewhere/outthere](http://example.com/somewhere/outthere) and so should [www.example.com/asdf.html?id=5&view=dashboard#report](http://www.example.com/asdf.html?id=5&view=dashboard#report)."""

        # when
        converted = tw.fix_links(content, current_category)

        # then
        self.assertEqual(converted, expected)

    #
    # helpers
    #

    @classmethod
    def extractFiles(cls, file_name, repo_name):
        file_path = os.path.join(TestTwPreprocessor.resources_dir, file_name)

        # 1) unzip the repo files
        temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = file_path

        # 2) Get the resource container
        rc = RC(repo_dir)

        return rc, repo_dir, temp_dir
