from __future__ import absolute_import, unicode_literals, print_function
import os
import tempfile
import unittest
import mock
import json
from six import BytesIO
from libraries.general_tools import url_utils


class UrlUtilsTests(unittest.TestCase):

    def setUp(self):
        """Runs before each test."""
        self.tmp_file = ""

    def tearDown(self):
        """Runs after each test."""
        # delete temp files
        if os.path.isfile(self.tmp_file):
            os.remove(self.tmp_file)

    @staticmethod
    def mock_urlopen(url):
        return BytesIO(("hello " + url).encode("ascii"))

    @staticmethod
    def raise_urlopen(url):
        raise IOError("An error occurred")

    def test_get_url(self):
        self.assertEqual(url_utils._get_url("world",
                                            catch_exception=False,
                                            urlopen=self.mock_urlopen),
                         "hello world")
        self.assertEqual(url_utils._get_url("world",
                                            catch_exception=True,
                                            urlopen=self.mock_urlopen),
                         "hello world")

    def test_get_url_error(self):
        self.assertFalse(url_utils._get_url("world",
                                            catch_exception=True,
                                            urlopen=self.raise_urlopen))
        self.assertRaises(IOError, url_utils._get_url,
                          "world", catch_exception=False, urlopen=self.raise_urlopen)

    def test_download_file(self):
        self.tmp_file = tempfile.mktemp()
        url_utils._download_file("world", self.tmp_file, self.mock_urlopen)
        with open(self.tmp_file, "r") as tmpf:
            self.assertEqual(tmpf.read(), "hello world")

    def test_join_url_parts_single(self):
        for part in ("foo", "/foo", "foo/", "/foo/"):
            self.assertEqual(url_utils.join_url_parts(part), part)

    def test_join_url_parts_multiple(self):
        self.assertEqual(url_utils.join_url_parts("foo/", "bar", "baz/qux/"),
                         "foo/bar/baz/qux/")

    @mock.patch('libraries.general_tools.url_utils._get_url')
    def test_get_languages(self, mock_get_url):
        languages = [
            {'gw': False, 'ld': 'ltr', 'ang': 'Afar', 'lc': 'aa', 'ln': 'Afaraf', 'lr': 'Africa', 'pk': 6},
            {'gw': True, 'ld': 'ltr', 'ang': 'English', 'lc': 'en', 'ln': 'English',
             'lr': 'Europe', 'pk': 1747},
            {'gw': True, 'ld': 'ltr', 'ang': 'Spanish', 'lc': 'es', 'ln': 'espa\xf1ol',
             'lr': 'Europe', 'pk': 1776},
            {'gw': True, 'ld': 'ltr', 'ang': 'French', 'lc': 'fr', 'ln': 'fran\xe7ais, langue fran\xe7aise',
             'lr': 'Europe', 'pk': 1868}
        ]
        mock_get_url.return_value = json.dumps(languages)
        self.assertEqual(len(url_utils.get_languages()), len(languages))
