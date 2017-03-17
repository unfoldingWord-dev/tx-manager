from __future__ import absolute_import, unicode_literals, print_function
import os
import shutil
import tempfile
import unittest
from unittest import TestCase
from aws_tools.s3_handler import S3Handler


class S3HandlerTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix='s3HandlerTest_')

    def tearDown(self):
        shutil.rmtree(self.temp_dir+'asdfa', ignore_errors=True)

    @unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true", "Skipping this test on Travis CI.")
    def test_download_dir(self):
        handler = S3Handler(bucket_name='test-tx-manager')
        handler.download_dir('test-s3-handler-download-dir', self.temp_dir)
        self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, 'test-s3-handler-download-dir', 'test.json')))
