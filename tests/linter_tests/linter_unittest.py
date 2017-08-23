from __future__ import print_function, unicode_literals
import unittest
import mock


class LinterTestCase(unittest.TestCase):

    def run(self, result=None):
        # Patch get_languages() in td_languages for every test case so that it never fetches the actual language json
        patcher = mock.patch('libraries.door43_tools.td_language.TdLanguage.get_languages')
        mock_get_languages = patcher.start()
        mock_get_languages.return_value = [
            {'gw': False, 'ld': 'ltr', 'ang': 'Afar', 'lc': 'aa', 'ln': 'Afaraf', 'lr': 'Africa', 'pk': 6},
            {'gw': True, 'ld': 'ltr', 'ang': 'English', 'lc': 'en', 'ln': 'English',
             'lr': 'Europe', 'pk': 1747},
            {'gw': True, 'ld': 'ltr', 'ang': 'Spanish', 'lc': 'es', 'ln': 'espa\xf1ol',
             'lr': 'Europe', 'pk': 1776},
            {'gw': True, 'ld': 'ltr', 'ang': 'French', 'lc': 'fr', 'ln': 'fran\xe7ais, langue fran\xe7aise',
             'lr': 'Europe', 'pk': 1868}
        ]

        super(LinterTestCase, self).run(result)

        patcher.stop()
