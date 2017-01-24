import tempfile
from six import BytesIO
import unittest

from general_tools import url_utils


class UrlUtilsTests(unittest.TestCase):

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
        tmp_file = tempfile.mktemp()
        url_utils._download_file("world", tmp_file, self.mock_urlopen)
        with open(tmp_file, "r") as tmpf:
            self.assertEqual(tmpf.read(), "hello world")

    def test_join_url_parts_single(self):
        for part in ("foo", "/foo", "foo/", "/foo/"):
            self.assertEqual(url_utils.join_url_parts(part), part)

    def test_join_url_parts_multiple(self):
        self.assertEqual(url_utils.join_url_parts("foo/", "bar", "baz/qux/"),
                         "foo/bar/baz/qux/")
