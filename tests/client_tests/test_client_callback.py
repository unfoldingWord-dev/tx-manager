from __future__ import absolute_import, unicode_literals, print_function

import json
import tempfile

import os
import mock
import shutil

from general_tools import file_utils
from mock import patch
from unittest import TestCase
from client.client_callback import ClientCallback


class TestClientCallback(TestCase):
    base_temp_dir = os.path.join(tempfile.gettempdir(), 'tx-manager')
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    source_zip = ''
    build_log_json = ''
    project_json = ''
    transfered_files = []  # for keeping track of file translfers to cdn

    def setUp(self):
        try:
            os.makedirs(TestClientCallback.base_temp_dir)
        except:
            pass

        self.temp_dir = tempfile.mkdtemp(dir=TestClientCallback.base_temp_dir, prefix='callbackTest_')
        TestClientCallback.transfered_files = []

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clientCallbackSimpleJob(self):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a'
        mock_ccb = self.mockClientCallback(identifier)

        # when
        results = mock_ccb.process_callback()

        # then
        self.assertIsNotNone(results)

    def test_clientCallbackMultipleJobPartial(self):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a/2/1/01-GEN.usfm'
        self.generate_parts_completed(1, 2)
        mock_ccb = self.mockClientCallback(identifier)

        # when
        results = mock_ccb.process_callback()

        # then
        self.assertIsNotNone(results)

    def test_clientCallbackMultipleJobComplete(self):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a/2/0/01-GEN.usfm'
        self.generate_parts_completed(0, 2)
        mock_ccb = self.mockClientCallback(identifier)

        # when
        results = mock_ccb.process_callback()

        # then
        self.assertIsNotNone(results)

    def test_clientCallbackMultipleNoJobsComplete(self):
        # given
        self.source_zip = os.path.join(self.resources_dir, "raw_sources/en-ulb.zip")
        identifier = 'tx-manager-test-data/en-ulb/22f3d09f7a/2/0/01-GEN.usfm'
        self.generate_parts_completed(0, 0)
        mock_ccb = self.mockClientCallback(identifier)

        # when
        results = mock_ccb.process_callback()

        # then
        self.assertIsNotNone(results)

    # helpers

    def mockClientCallback(self, identifier):
        self.build_log_json = {
            'dummy_data': 'stuff',
            'commit_id':  '123456ff',
            'created_at': '2017-05-22T13:39:15Z',
            'started_at': '2017-05-22T13:39:16Z',
            'repo_owner': 'repo_owner1',
            'repo_name':  'repo_name2',
        }
        self.build_log_json = json.dumps(self.build_log_json)

        self.project_json = '{}'

        vars = {
            'job_data': {
                'created_at': '2017-05-22T13:39:15Z',
                'identifier': ('%s' % identifier),
                'output':     'https://test-cdn.door43.org/tx/job/6864ae1b91195f261ba5cda62d58d5ad9333f3131c787bb68f20c27adcc85cad.zip',
                'ended_at':   '2017-05-22T13:39:17Z',
                'started_at': '2017-05-22T13:39:16Z',
                'status':     'started',
                'success':    'success'
            },
            'gogs_url': 'https://git.example.com',
            'cdn_bucket': 'cdn_test_bucket'
        }
        mock_ccb = ClientCallback(**vars)
        mock_ccb.download_file = self.mock_downloadFile
        mock_ccb.cdn_upload_file = self.mock_cdn_upload_file
        mock_ccb.cdn_get_json_file = self.mock_cdnGetJsonFile
        mock_ccb.get_finished_parts = self.mock_get_finished_parts
        mock_ccb.cdn_download_file = self.mock_cdnDownloadFile
        return mock_ccb

    def mock_downloadFile(self, target, url):
        file_name = os.path.basename(url)
        if '.zip' in file_name:
            shutil.copyfile(self.source_zip, target)
        elif file_name == 'build_log.json':
            file_utils.write_file(target, self.build_log_json)
        elif file_name == 'project.json':
            file_utils.write_file(target, self.project_json)

    def mock_cdn_upload_file(self, cdn_handler, project_file, s3_key, cache_time=600):
        bucket_name = cdn_handler.bucket.name
        TestClientCallback.transfered_files.append({'type': 'upload', 'file': project_file,
                                                    'key': bucket_name + '/' + s3_key})
        return

    def mock_cdnGetJsonFile(self, cdn_handler, s3_key):
        bucket_name = cdn_handler.bucket.name
        TestClientCallback.transfered_files.append({'type': 'download', 'file': 'json',
                                                    'key': bucket_name + '/' + s3_key})
        if 'build_log.json' in s3_key:
            return json.loads(self.build_log_json)
        elif 'project.json' in s3_key:
            return json.loads(self.project_json)
        return ''

    def generate_parts_completed(self, start, end):
        TestClientCallback.parts = []
        for i in range(start, end):
            part = Part("{0}.finished".format(i))
            TestClientCallback.parts.append(part)
        return TestClientCallback.parts

    def mock_get_finished_parts(self, cdn_handler, s3_commit_key):
        return TestClientCallback.parts

    def mock_cdnDownloadFile(self, cdn_handler, s3_part_key, target):
        bucket_name = cdn_handler.bucket.name
        self.mock_downloadFile(target, s3_part_key)
        TestClientCallback.transfered_files.append({'type': 'download', 'file': target,
                                                    'key': bucket_name + '/' + s3_part_key})


class Part(object):
    def __init__(self, key):
        self.key = key
