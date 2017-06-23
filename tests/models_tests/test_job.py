from __future__ import absolute_import, unicode_literals, print_function
from unittest import TestCase
from moto import mock_dynamodb2
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.models.job import TxJob


@mock_dynamodb2
class TxJobTests(TestCase):
    JOB_TABLE_NAME = 'tx-job'
    setup_table = False

    def setUp(self):
        self.db_handler = DynamoDBHandler(TxJobTests.JOB_TABLE_NAME)
        if not TxJobTests.setup_table:
            self.init_table()
            TxJobTests.setup_table = True
        self.items = {}
        self.init_items()
        self.populate_table()

    def init_table(self):
        self.db_handler.resource.create_table(
            TableName=TxJobTests.JOB_TABLE_NAME,
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
            TxJob(db_handler=self.db_handler).insert(self.items[idx])

    def test_query_job(self):
        jobs = TxJob(db_handler=self.db_handler).query()
        self.assertEqual(len(jobs), len(self.items))
        self.maxDiff = None
        for job in jobs:
            self.assertEqual(job.get_db_data(), TxJob(self.items[job.job_id]).get_db_data())

    def test_update_job(self):
        job = TxJob(db_handler=self.db_handler).load({'job_id': self.items['job3']['job_id']})
        job.status = 'finished'
        job.update()
        job.load()
        self.assertEqual(job.status, 'finished')

    def test_delete_job(self):
        job = TxJob(db_handler=self.db_handler).load({'job_id': self.items['job1']['job_id']})
        self.assertIsNotNone(job.job_id)
        job.delete()
        job.load()
        self.assertIsNone(job.job_id)
