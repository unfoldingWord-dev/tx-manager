from __future__ import print_function, unicode_literals
import unittest
from libraries.door43_tools.td_language import TdLanguage


class LinterTestCase(unittest.TestCase):

    def run(self, result=None):
        # Doing this for all linter test cases
        TdLanguage.language_list = {
            'aa': TdLanguage({'gw': False, 'ld': 'ltr', 'ang': 'Afar', 'lc': 'aa', 'ln': 'Afaraf', 'lr': 'Africa', 'pk': 6}),
            'en': TdLanguage({'gw': True, 'ld': 'ltr', 'ang': 'English', 'lc': 'en', 'ln': 'English',
             'lr': 'Europe', 'pk': 1747}),
            'es': TdLanguage({'gw': True, 'ld': 'ltr', 'ang': 'Spanish', 'lc': 'es', 'ln': 'espa\xf1ol',
             'lr': 'Europe', 'pk': 1776}),
            'fr': TdLanguage({'gw': True, 'ld': 'ltr', 'ang': 'French', 'lc': 'fr', 'ln': 'fran\xe7ais, langue fran\xe7aise',
             'lr': 'Europe', 'pk': 1868})
        }


        super(LinterTestCase, self).run(result)

