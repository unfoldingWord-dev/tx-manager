from __future__ import absolute_import, unicode_literals, print_function
import unittest
from libraries.linters.linter_handler import LinterHandler


class TestLinterHandler(unittest.TestCase):

    def test_get_linter_class(self):
        self.assertEqual(LinterHandler('obs').get_linter_class().__name__, 'ObsLinter')
        self.assertEqual(LinterHandler('ta').get_linter_class().__name__, 'TaLinter')
        self.assertEqual(LinterHandler('tn').get_linter_class().__name__, 'TnLinter')
        self.assertEqual(LinterHandler('tq').get_linter_class().__name__, 'TqLinter')
        self.assertEqual(LinterHandler('tw').get_linter_class().__name__, 'TwLinter')
        self.assertEqual(LinterHandler('udb').get_linter_class().__name__, 'UdbLinter')
        self.assertEqual(LinterHandler('ulb').get_linter_class().__name__, 'UlbLinter')
        self.assertEqual(LinterHandler('bible').get_linter_class().__name__, 'UsfmLinter')
        self.assertEqual(LinterHandler('something').get_linter_class().__name__, 'MarkdownLinter')
        self.assertEqual(LinterHandler('').get_linter_class().__name__, 'MarkdownLinter')
