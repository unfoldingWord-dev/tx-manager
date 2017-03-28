from __future__ import absolute_import, unicode_literals, print_function
import os
import shutil
import tempfile
import unittest
from botocore.exceptions import ClientError
from unittest import TestCase
from aws_tools.s3_handler import S3Handler


class S3HandlerTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='s3HandlerTest_')
        self.handler = S3Handler(bucket_name='test-tx-manager')

    def tearDown(self):
        shutil.rmtree(self.temp_dir+'asdfa', ignore_errors=True)

    def test_setup_resources(self):
        myHandler = S3Handler(aws_access_key_id='access_key', aws_secret_access_key='secret_key', aws_region_name='us-west-1')
        self.assertEqual(myHandler.aws_access_key_id, 'access_key')
        self.assertEqual(myHandler.aws_secret_access_key, 'secret_key')
        self.assertEqual(myHandler.aws_region_name, 'us-west-1')

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_download_dir(self):
        self.handler.download_dir('test-s3-handler-download-dir', self.temp_dir)
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, 'test-s3-handler-download-dir', 'test.json')))
        shutil.rmtree(os.path.join(self.temp_dir, 'test-s3-handler-download-dir'), ignore_errors=True)

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_key_exists(self):
        self.assertTrue(self.handler.key_exists('test-s3-handler-key-exists/exists.json'))

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_key_does_not_exists(self):
        self.assertFalse(self.handler.key_exists(key='test-s3-handler-key-exists/does_not_exists.json', bucket_name='test-tx-manager'))

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_key_exists_bad_bucket(self):
        self.assertRaises(ClientError, self.handler.key_exists, key='test-s3-handler-key-exists/does_not_exists.json', bucket_name='bad_bucket')

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_copy_good(self):
        ret = self.handler.copy(from_key="from_dir/from_file", to_key="to_dir/to_file", from_bucket="test-tx-manager2")
        self.assertTrue(ret)

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_copy_bad(self):
        ret = self.handler.copy(from_key="from_bad_dir/from_bad_file")
        self.assertFalse(ret)
        self.assertRaises(Exception, self.handler.copy, from_key="from_bad_dir/from_bad_file", catch_exception=False)

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_get_file_contents_good(self):
        self.assertEqual('test\n', self.handler.get_file_contents("test-s3-handler-get-file-contents/test.txt"))

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_get_file_contents_bad(self):
        ret = self.handler.get_file_contents("from_bad_dir/from_bad_file")
        self.assertFalse(ret)
        self.assertRaises(Exception, self.handler.get_file_contents, key="from_bad_dir/from_bad_file", catch_exception=False)
