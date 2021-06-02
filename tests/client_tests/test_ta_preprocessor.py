from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import shutil
import markdown2
from libraries.resource_container.ResourceContainer import RC
from libraries.client.preprocessors import do_preprocess, TaPreprocessor
from libraries.general_tools.file_utils import unzip, read_file
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
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '01-intro.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '02-process.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '03-translate.md')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '04-checking.md')))
        intro = read_file(os.path.join(self.out_dir, '01-intro.md'))
        process = read_file(os.path.join(self.out_dir, '02-process.md'))
        translate = read_file(os.path.join(self.out_dir, '03-translate.md'))
        checking = read_file(os.path.join(self.out_dir, '04-checking.md'))
        soup = BeautifulSoup(markdown2.markdown(checking, extras=['markdown-in-html', 'tables']), 'html.parser')
        self.assertEqual(soup.h1.text, "Checking Manual")
        self.assertIsNotNone(soup.find("a", {"id": "accurate"}))
        self.assertEqual(len(soup.find_all('li')), 350)
        # Test links have been converted
        self.assertIsNotNone(soup.find("a", {"href": "#accuracy-check"}))
        self.assertIsNotNone(soup.find("a", {"href": "03-translate.html#figs-explicit"}))
        # make sure no old links exist
        self.assertTrue('../' not in checking)
        self.assertTrue('../' not in intro)
        self.assertTrue('../' not in process)
        self.assertTrue('../' not in translate)
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '04-checking-toc.yaml')))
        self.assertTrue(os.path.isfile(os.path.join(self.out_dir, '04-checking-config.yaml')))
        preprocessor = TaPreprocessor(rc, repo_dir, self.out_dir)
        self.assertEqual(preprocessor.get_title(rc.project('checking'), 'fake-link', 'My Title'), 'My Title')
        self.assertEqual(preprocessor.get_title(rc.project('checking'), 'fake-link'), 'Fake Link')

    def test_fix_links(self):
        rc = RC(os.path.join(self.resources_dir, 'manifests', 'ta'))
        ta = TaPreprocessor(rc, tempfile.gettempdir(), tempfile.gettempdir())

        content = "This has [links](../section1/01.md) to the same [manual](../section2/01.md)"
        expected = "This has [links](#section1) to the same [manual](#section2)"

        converted = ta.fix_links(content)
        self.assertEqual(converted, expected)

        ################################################################################################################

        content = """This has links to 
        [other](../../checking/section1/01.md) [manuals](../../translate/section2/01.md)"""
        expected = """This has links to 
        [other](04-checking.html#section1) [manuals](03-translate.html#section2)"""

        converted = ta.fix_links(content)
        self.assertEqual(converted, expected)

        ################################################################################################################

        content = """This has links to both this [manual](../section1/01.md),
         this [page](section2) and [another manual](../../process/section3/01.md)."""
        expected = """This has links to both this [manual](#section1),
         this [page](#section2) and [another manual](02-process.html#section3)."""

        converted = ta.fix_links(content)
        self.assertEqual(converted, expected)

        ################################################################################################################

        content = """This link should NOT be converted: [webpage](http://example.com/somewhere/outthere) """
        expected = """This link should NOT be converted: [webpage](http://example.com/somewhere/outthere) """

        converted = ta.fix_links(content)
        self.assertEqual(converted, expected)

        ################################################################################################################

        # content = """This [link](rc://en/tw/dict/bible/other/dream) is a rc link that should go to
        #     other/dream.md in the en_tw repo"""
        # expected = """This [link](https://git.door43.org/Door43/en_tw/src/master/bible/other/dream.md) is a rc link that should go to
        #     other/dream.md in the en_tw repo"""
        content = """
        [link](rc://as/tn/help/rut/04/14)
        [link](rc://en/tn/help/1co/05/14)
        [link](rc://fr/tn/help/1co/06/14)
        [link](rc://fr/tn/help/1co/07/14)
        [link](rc://fr/tn/help/1co/08/14)
        """
        expected = """
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/as_tn/5ec1fb81f6/8-RUT.html#tn-chunk-rut-004-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/en_tn/ccdb2a707b/47-1CO.html#tn-chunk-1co-005-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/fr_tn/5f066d1aab/47-1CO.html#tn-chunk-1co-006-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/fr_tn/5f066d1aab/47-1CO.html#tn-chunk-1co-007-014)
        [link](http://read.bibletranslationtools.org/u/WA-Catalog/fr_tn/5f066d1aab/47-1CO.html#tn-chunk-1co-008-014)
        """

        converted = ta.fix_links(content)
        self.assertEqual(expected, converted)

        ################################################################################################################

        content = """This url should be made into a link: http://example.com/somewhere/outthere and so should www.example.com/asdf.html?id=5&view=dashboard#report."""
        expected = """This url should be made into a link: [http://example.com/somewhere/outthere](http://example.com/somewhere/outthere) and so should [www.example.com/asdf.html?id=5&view=dashboard#report](http://www.example.com/asdf.html?id=5&view=dashboard#report)."""

        converted = ta.fix_links(content)
        self.assertEqual(converted, expected)

        ################################################################################################################

        # Tests https://git.door43.org/Door43/en_ta/raw/master/translate/translate-source-text/01.md
        content = """
### Factors to Consider for a Source Text

When choosing a source text, there are a number of factors that must be considered:

  * **[Statement of Faith](../../intro/statement-of-faith/01.md)** - Is the text in line with the Statement of Faith?
  * **[Translation Guidelines](../../intro/translation-guidelines/01.md)** - Is the text in line with the Translation Guidelines?
  * **Language** - Is the text in a suitable language that translators and checkers understand well?
  * **[Copyrights, Licensing, and Source Texts](../translate-source-licensing/01.md)** - Is the text released under a license that gives sufficient legal freedom?
  * **[Source Texts and Version Numbers](../translate-source-version/01.md)** - Is the text the latest, most updated version?
  * **[The Original and Source Languages](../translate-original/01.md)** - Does the translation team understand the difference between source languages and original languages?
  * **[Original Manuscripts](../translate-manuscripts/01.md)** - Does the translation team understand about Original Manuscripts and [Textual Variants](../translate-textvariants/01.md)?

It is important the the leaders of the churches in the language group agree that the source text is a good one. The Open Bible Stories are available in many source languages on http://ufw.io/stories/. There are also translations of the Bible there to be used as sources for translation in English, and soon other languages, as well.
"""
        expected = """
### Factors to Consider for a Source Text

When choosing a source text, there are a number of factors that must be considered:

  * **[Statement of Faith](01-intro.html#statement-of-faith)** - Is the text in line with the Statement of Faith?
  * **[Translation Guidelines](01-intro.html#translation-guidelines)** - Is the text in line with the Translation Guidelines?
  * **Language** - Is the text in a suitable language that translators and checkers understand well?
  * **[Copyrights, Licensing, and Source Texts](#translate-source-licensing)** - Is the text released under a license that gives sufficient legal freedom?
  * **[Source Texts and Version Numbers](#translate-source-version)** - Is the text the latest, most updated version?
  * **[The Original and Source Languages](#translate-original)** - Does the translation team understand the difference between source languages and original languages?
  * **[Original Manuscripts](#translate-manuscripts)** - Does the translation team understand about Original Manuscripts and [Textual Variants](#translate-textvariants)?

It is important the the leaders of the churches in the language group agree that the source text is a good one. The Open Bible Stories are available in many source languages on [http://ufw.io/stories/](http://ufw.io/stories/). There are also translations of the Bible there to be used as sources for translation in English, and soon other languages, as well.
"""
        converted = ta.fix_links(content)
        self.assertEqual(converted, expected)

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
