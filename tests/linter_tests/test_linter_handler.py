from __future__ import absolute_import, unicode_literals, print_function
import unittest
from libraries.linters.linter_handler import LinterHandler
from libraries.resource_container.ResourceContainer import RC


class TestLinterHandler(unittest.TestCase):

    def test_get_linter_class(self):
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_obs')).get_linter_class().__name__, 'ObsLinter')
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_ta')).get_linter_class().__name__, 'TaLinter')
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_tn')).get_linter_class().__name__, 'TnLinter')
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_tq')).get_linter_class().__name__, 'TqLinter')
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_tw')).get_linter_class().__name__, 'TwLinter')
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_udb')).get_linter_class().__name__, 'UdbLinter')
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_ulb')).get_linter_class().__name__, 'UlbLinter')
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_bible')).get_linter_class().__name__, 'UsfmLinter')
        self.assertEqual(LinterHandler(rc=RC(repo_name='fr_something')).get_linter_class().__name__, 'MarkdownLinter')
        self.assertEqual(LinterHandler(rc=RC()).get_linter_class().__name__, 'MarkdownLinter')
