from __future__ import absolute_import, unicode_literals, print_function
import unittest
from libraries.checkers.checker import Checker


class TestChecker(unittest.TestCase):

    def test_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Checker, None, None)
