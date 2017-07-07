from __future__ import absolute_import, unicode_literals, print_function
import unittest
from libraries.checkers.checker_handler import get_checker


class TestCheckerHandler(unittest.TestCase):

    def test_instantiate_abstract_class(self):
        self.assertEqual(get_checker('bible').__name__, 'BibleChecker')
        self.assertEqual(get_checker('obs').__name__, 'ObsChecker')
        self.assertEqual(get_checker('ta').__name__, 'TaChecker')
        self.assertEqual(get_checker('tn').__name__, 'TnChecker')
        self.assertEqual(get_checker('tq').__name__, 'TqChecker')
        self.assertEqual(get_checker('tw').__name__, 'TwChecker')
        self.assertEqual(get_checker('udb').__name__, 'UdbChecker')
        self.assertEqual(get_checker('ulb').__name__, 'UlbChecker')
        self.assertEqual(get_checker('something'), None)
