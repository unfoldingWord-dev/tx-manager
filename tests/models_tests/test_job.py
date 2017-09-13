from __future__ import absolute_import, unicode_literals, print_function
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.models.job import TxJob
from libraries.app.app import App


@mock_dynamodb2
class TxJobTests(TestCase):
    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        self.init_table()
        self.items = {}
        self.init_items()
        self.populate_table()

    def init_table(self):
        try:
            App.job_db_handler.table.delete()
        except:
            pass
        App.job_db_handler.resource.create_table(
            TableName=App.job_table_name,
            KeySchema=[
                {
                    'AttributeName': 'job_id',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'job_id',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )

    def init_items(self):
        self.items = {
            'job1': {
                'job_id': 'job1',
                'status': 'started',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'errors': []
            },
            'job2': {
                'job_id': 'job2',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'errors': ['error'],
                'cdn_bucket': 'cdn.door43.org',
                'identifier': 'tx-manager-test-data/en-ulb-jud/6778aa89bd',
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bd.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750d.zip',
                'created_at':	'2017-04-12T17:03:06Z'
            },
            'job3': {
                'job_id': 'job3',
                'status': 'requested',
                'resource_type': 'ulb',
                'input_format': 'usfm',
                'output_format': 'html',
                'callback': None,
                'convert_module': 'module1',
                'warnings': []
            },
        }

    def populate_table(self):
        for idx in self.items:
            TxJob().insert(self.items[idx])

    def test_query_job(self):
        jobs = TxJob().query()
        App.logger.debug(jobs)
        self.assertEqual(len(jobs), len(self.items))
        for job in jobs:
            self.assertEqual(job.get_db_data(), TxJob(self.items[job.job_id]).get_db_data())

    def test_load_job(self):
        # Test loading by just giving it the job_id in the constructor
        job = TxJob('job1')
        self.assertEqual(job.get_db_data(), TxJob(self.items['job1']).get_db_data())
        # Test loading by just giving it only the job_id in the data array in the constructor
        job = TxJob({'job_id': 'job2'})
        self.assertEqual(job.get_db_data(), TxJob(self.items['job2']).get_db_data())

    def test_update_job(self):
        job = TxJob().load({'job_id': self.items['job3']['job_id']})
        job.status = 'finished'
        job.update()
        job.load()
        self.assertEqual(job.status, 'finished')

    def test_delete_job(self):
        job = TxJob().load({'job_id': self.items['job1']['job_id']})
        self.assertIsNotNone(job.job_id)
        job.delete()
        job.load()
        self.assertIsNone(job.job_id)
