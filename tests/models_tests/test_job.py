from __future__ import absolute_import, unicode_literals, print_function
from unittest import TestCase
from datetime import datetime, timedelta
from libraries.models.job import TxJob
from libraries.app.app import App


class TxJobTests(TestCase):
    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        self.items = {}
        self.init_items()
        self.populate_table()

    def init_items(self):
        self.items = {
            'job1': {
                'job_id': 'job1',
                'identifier': 'user1/repo1/commit1',
                'user_name': 'user1',
                'repo_name': 'repo1',
                'commit_id': 'commit1',
                'user': 'user1',
                'status': 'started',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'convert_md2html',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=1),
                'started_at': None,
                'ended_at': None,
                'eta': datetime.utcnow() + timedelta(minutes=5),
                'source': 'https://some/url',
                'output': 'u/user1/repo1',
                'cdn_bucket': 'cdn.door43.org',
                'cdn_file': 'u/user1/repo1',
                'callback': 'https://client/callback',
                'links': {'link': 'https://some/link'},
                'success': False,
                'message': 'Started',
                'log': ['Started job'],
                'warnings': ['Linter warning'],
                'errors': []
            },
            'job2': {
                'job_id': 'job2',
                'identifier': 'tx-manager-test-data/en-ulb-jud/6778aa89bd',
                'user_name': 'tx-manager-test-data',
                'repo_name': 'en-ulb-jud',
                'commit_id': '6778aa89bd',
                'user': 'user1',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'cdn_bucket': 'cdn.door43.org',
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bd.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750d.zip',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=1),
                'started_at': None,
                'ended_at': None,
                'eta': datetime.utcnow() + timedelta(minutes=5),
                'cdn_file': 'u/user1/repo1',
                'callback': 'https://client/callback',
                'links': {'link': 'https://some/link'},
                'success': False,
                'message': 'Requested',
                'log': ['Requestedjob'],
                'warnings': ['Linter warning'],
                'errors': ['error']
            },
            'job3': {
                'job_id': 'job3',
                'identifier': 'user1/repo1/commit1',
                'user_name': 'user1',
                'repo_name': 'repo1',
                'commit_id': 'commit1',
                'user': 'user1',
                'status': 'requested',
                'resource_type': 'ulb',
                'input_format': 'usfm',
                'output_format': 'html',
                'callback': None,
                'convert_module': 'module1',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(days=1),
                'started_at': None,
                'ended_at': None,
                'eta': datetime.utcnow() + timedelta(minutes=5),
                'source': 'https://some/url',
                'output': 'u/user1/repo1',
                'cdn_bucket': 'cdn.door43.org',
                'cdn_file': 'u/user1/repo1',
                'links': {'link': 'https://some/link'},
                'success': False,
                'message': 'Requested',
                'log': ['Requested job'],
                'warnings': [],
                'errors': []
            },
        }

    def populate_table(self):
        for idx in self.items:
            tx_job = TxJob(**self.items[idx])
            tx_job.insert()

    def test_query_job(self):
        jobs = TxJob.query()
        App.logger.debug(jobs)
        self.assertEqual(jobs.count(), len(self.items))
        for job in jobs:
            print(job)
            self.assertEqual(job.identifier, self.items[job.job_id]['identifier'])

    def test_load_job(self):
        # Test loading by just giving it the job_id in the constructor
        job = TxJob.get('job1')
        self.assertEqual(job.identifier, self.items['job1']['identifier'])

    def test_update_job(self):
        job = TxJob.get(self.items['job3']['job_id'])
        job.status = 'finished'
        job.update()
        job = TxJob.get(self.items['job3']['job_id'])
        self.assertEqual(job.status, 'finished')

    def test_delete_job(self):
        job = TxJob.get(self.items['job1']['job_id'])
        self.assertIsNotNone(job)
        job.delete()
        job = TxJob.get(self.items['job1']['job_id'])
        self.assertIsNone(job)
