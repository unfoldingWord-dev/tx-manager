from __future__ import absolute_import, unicode_literals, print_function
import unittest
import mock
import json
from libraries.door43_tools.td_language import TdLanguage


class TdLanguageTest(unittest.TestCase):
    def test_init(self):
        language = TdLanguage({'lc': 'test', 'ln': 'Test Language', 'ld': 'rtl'})
        self.assertEqual(language.ln, 'Test Language')
        self.assertEqual(language.ld, 'rtl')

    @mock.patch('libraries.general_tools.url_utils._get_url')
    def test_get_languages(self, mock_get_url):
        expected_languages = [
            {'gw': False, 'ld': 'ltr', 'ang': 'Afar', 'lc': 'aa', 'ln': 'Afaraf', 'lr': 'Africa', 'pk': 6},
            {'gw': True, 'ld': 'ltr', 'ang': 'English', 'lc': 'en', 'ln': 'English',
             'lr': 'Europe', 'pk': 1747},
            {'gw': True, 'ld': 'ltr', 'ang': 'Spanish', 'lc': 'es', 'ln': 'espa\xf1ol',
             'lr': 'Europe', 'pk': 1776},
            {'gw': True, 'ld': 'ltr', 'ang': 'French', 'lc': 'fr', 'ln': 'fran\xe7ais, langue fran\xe7aise',
             'lr': 'Europe', 'pk': 1868}
        ]
        mock_get_url.return_value = json.dumps(expected_languages)
        languages = TdLanguage.get_languages()
        self.assertTrue('fr' in languages)
        self.assertEqual(len(languages), len(expected_languages))

    def test_get_language(self):
        language = TdLanguage.get_language('aa')
        self.assertIsNotNone(language)
        self.assertEqual(language.ln, 'Afaraf')

if __name__ == "__main__":
    unittest.main()
