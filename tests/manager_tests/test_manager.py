from __future__ import absolute_import, unicode_literals, print_function
import json
import unittest
import mock
from bs4 import BeautifulSoup
from tests.manager_tests import mock_utils
from libraries.models.job import TxJob
from libraries.manager.manager import TxManager
from libraries.models.module import TxModule
from moto import mock_dynamodb2


@mock_dynamodb2
class ManagerTest(unittest.TestCase):
    MOCK_API_URL = 'https://api.example.com'
    MOCK_CDN_URL = 'https://cdn.example.com'
    MOCK_CALLBACK_URL = 'https://callback.example.com/'
    MOCK_GOGS_URL = 'https://mock.gogs.io'
    MOCK_CDN_BUCKET = 'mock_bucket'
    MOCK_JOB_TABLE_NAME = 'mock-job'
    MOCK_MODULE_TABLE_NAME = 'mock-module'

    mock_gogs = None
    setup_tables = False
    
    tx_manager_env_vars = {
        'api_url': MOCK_API_URL,
        'cdn_url': MOCK_CDN_URL,
        'gogs_url': MOCK_GOGS_URL,
        'cdn_bucket': MOCK_CDN_BUCKET,
        'job_table_name': MOCK_JOB_TABLE_NAME,
        'module_table_name': MOCK_MODULE_TABLE_NAME
    }

    patches = []
    requested_urls = []

    @classmethod
    def setUpClass(cls):
        cls.mock_gogs = mock.MagicMock(
            return_value=mock_utils.mock_gogs_handler(['token1', 'token2']))
        ManagerTest.patches = (
            mock.patch('libraries.manager.manager.GogsHandler', cls.mock_gogs),
        )
        for patch in ManagerTest.patches:
            patch.start()

    def setUp(self):
        self.tx_manager = TxManager(**self.tx_manager_env_vars)
        ManagerTest.mock_gogs.reset_mock()
        ManagerTest.requested_urls = []
        if not ManagerTest.setup_tables:
            self.init_tables()
            ManagerTest.setup_tables = True
        self.job_items = {}
        self.module_items = {}
        self.init_items()
        self.populate_tables()

    def init_tables(self):
        self.tx_manager.job_db_handler.resource.create_table(
            TableName=ManagerTest.MOCK_JOB_TABLE_NAME,
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
        self.tx_manager.module_db_handler.resource.create_table(
            TableName=ManagerTest.MOCK_MODULE_TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )

    def init_items(self):
        self.job_items = {
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
                'callback': ManagerTest.MOCK_CALLBACK_URL,
                'convert_module': 'module1',
                'warnings': []
            },
            'job4': {
                'job_id': 'job4',
                'status': 'requested',
                'resource_type': 'other',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'warnings': ['warning' ]
            },
            'job5': {
                'job_id': 'job5',
                'status': 'requested',
                'resource_type': 'unsupported',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'warnings': ['warning1', 'warning2' ]
            },
            'job7': {
                'job_id': 'job7',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module2'
            },
            'job8': {
                'job_id': 'job8',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module2'
            },
            'job9': {
                'job_id': 'job9',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'html',
                'output_format': 'pdf',
                'convert_module': 'module4'
            },
            'job10': {
                'job_id': 'job10',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module2',
                'identifier': 'tx-manager-test-data/en-ulb-jud/6778aa89bZ',
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bdZ.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750dZ.zip',
                'errors': ['error1', 'error2' ],
                'cdn_bucket': 'cdn.door43.org',
                'created_at':	'2017-03-12T17:03:076Z'
            },
            'job11': {
                'job_id': 'job11',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module2',
                'identifier': 'tx-manager-test-data/en-ulb-jud/6778aa89bZZ',
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bdZZ.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750dZZ.zip',
                'errors': ['error1','error2','error3' ],
                'cdn_bucket': 'cdn.door43.org',
                'created_at':	'2017-05-12T17:03:04Z'
            }
        }
        self.module_items = {
            'module1': {
                'name': 'module1',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['obs', 'ulb'],
                'input_format': 'md',
                'output_format': 'html',
                'public_links': ['{0}/tx/convert/md2html'.format(ManagerTest.MOCK_API_URL)],
                'private_links': ['{0}/tx/private/module1'.format(ManagerTest.MOCK_API_URL)],
                'options': {'pageSize': 'A4'}
            },
            'module2': {
                'name': 'module2',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['ulb'],
                'input_format': 'usfm',
                'output_format': 'html',
                'public_links': ['{0}/tx/convert/usfm2html'.format(ManagerTest.MOCK_API_URL)],
                'private_links': [],
                'options': {'pageSize': 'A4'}
            },
            'module3': {
                'name': 'module3',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['other', 'yet_another'],
                'input_format': 'md',
                'output_format': 'html',
                'public_links': [],
                'private_links': [],
                'options': {}
            }
        }

    def populate_tables(self):
        for idx in self.job_items:
            TxJob(db_handler=self.tx_manager.job_db_handler).insert(self.job_items[idx])
        for idx in self.module_items:
            TxModule(db_handler=self.tx_manager.module_db_handler).insert(self.module_items[idx])

    @classmethod
    def tearDownClass(cls):
        for patch in ManagerTest.patches:
            patch.stop()

    def test_setup_job(self):
        """Successful call of setup_job."""
        data = {
            'gogs_user_token': 'token1',
            'cdn_bucket':  'test_cdn_bucket',
            'source': 'test_source',
            'resource_type': 'obs',
            'input_format': 'md',
            'output_format': 'html'
        }
        ret = self.tx_manager.setup_job(data)
        # assert an entry was added to job database
        job = TxJob(db_handler=self.tx_manager.job_db_handler).load({'job_id': ret['job']['job_id']})
        self.assertEqual(job.convert_module, 'module1')
        self.assertEqual(job.resource_type, 'obs')
        self.assertEqual(job.cdn_bucket, 'test_cdn_bucket')

    def test_setup_job_bad_requests(self):
        """Tests bad calls of setup_job due to missing or bad input."""
        self.tx_manager.cdn_bucket = None

        # Missing gogs_user_token
        data = {
            'cdn_bucket':  'test_cdn_bucket',
            'source': 'test_source',
            'resource_type': 'obs',
            'input_format': 'md',
            'output_format': 'html'
        }
        self.assertRaises(Exception, self.tx_manager.setup_job, data)

        # Bad gogs_user_token
        data = {
            'gogs_user_token': 'bad_token',
            'cdn_bucket':  'test_cdn_bucket',
            'source': 'test_source',
            'resource_type': 'obs',
            'input_format': 'md',
            'output_format': 'html'
        }
        self.assertRaises(Exception, self.tx_manager.setup_job, data)

        # Missing cdn_bucket
        data = {
            'gogs_user_token': 'token1',
            'source': 'test_source',
            'resource_type': 'obs',
            'input_format': 'md',
            'output_format': 'html'
        }
        self.assertRaises(Exception, self.tx_manager.setup_job, data)

        # Missing source
        data = {
            'gogs_user_token': 'token1',
            'cdn_bucket':  'test_cdn_bucket',
            'resource_type': 'obs',
            'input_format': 'md',
            'output_format': 'html'
        }
        self.assertRaises(Exception, self.tx_manager.setup_job, data)

        # Missing resource_type
        self.tx_manager = TxManager(**self.tx_manager_env_vars)
        data = {
            'gogs_user_token': 'token1',
            'cdn_bucket':  'test_cdn_bucket',
            'source': 'test_source',
            'input_format': 'md',
            'output_format': 'html'
        }
        self.assertRaises(Exception, self.tx_manager.setup_job, data)

        # Missing input_format
        data = {
            'gogs_user_token': 'token1',
            'cdn_bucket':  'test_cdn_bucket',
            'source': 'test_source',
            'resource_type': 'obs',
            'output_format': 'html'
        }
        self.assertRaises(Exception, self.tx_manager.setup_job, data)

        # Missing output_format
        data = {
            'gogs_user_token': 'token1',
            'cdn_bucket':  'test_cdn_bucket',
            'source': 'test_source',
            'resource_type': 'obs',
            'input_format': 'md'
        }
        self.assertRaises(Exception, self.tx_manager.setup_job, data)

    def test_setup_job_malformed_input(self):
        """Call setup_job with malformed data arguments."""
        tx_manager = TxManager()
        data = {
            'gogs_user_token': 'token1',
            'cdn_bucket': 'test_cdn_bucket',
            'source': 'test_source',
            'resource_type': 'obs',
            'input_format': 'md',
            'output_format': 'html'
        }
        for key in data:
            # should raise an exception if data is missing a required field
            missing = data.copy()
            del missing[key]
            self.assertRaises(Exception, tx_manager.setup_job, missing)
        # should raise an exception if called with an invalid user_token
        bad_token = data.copy()
        bad_token['gogs_user_token'] = 'bad_token'
        self.assertRaises(Exception, tx_manager.setup_job, bad_token)

    def test_setup_job_no_converter(self):
        """Call setup_job when there is no applicable converter."""
        tx_manager = TxManager(**self.tx_manager_env_vars)
        data = {
            'gogs_user_token': 'token1',
            'cdn_bucket': 'test_cdn_bucket',
            'source': 'test_source',
            'resource_type': 'unrecognized_resource_type',
            'input_format': 'md',
            'output_format': 'html'
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

    # noinspection PyUnusedLocal
    @mock.patch('libraries.aws_tools.lambda_handler.LambdaHandler.invoke')
    @mock.patch('requests.post')
    def test_start_job1(self, mock_request_post, mock_invoke):
        """
        Call start job in job 1 from mock data.

        Should be a successful invocation with warnings.
        """
        payload = {
            'info': ['Converted!'],
            'warnings': ['Missing something'],
            'errors': [],
            'success': True,
            'message': 'Has some warnings'
        }
        mock_invoke.return_value = self.create_mock_payload(payload)

        mock_request_post.return_value = None

        self.tx_manager.start_job('job2')

        # job1's entry in database should have been updated
        job = TxJob(db_handler=self.tx_manager.job_db_handler).load({'job_id': 'job2'})
        self.assertEqual(job.job_id, 'job2')
        self.assertEqual(len(job.errors), 1)
        self.assertTrue(len(job.warnings) == 1)

    # noinspection PyUnusedLocal
    @mock.patch('libraries.aws_tools.lambda_handler.LambdaHandler.invoke')
    @mock.patch('requests.post')
    def test_start_job2(self, mock_request_post, mock_invoke):
        """
        Call start_job in job 2 from mock data.

        Should be a successful invocation without warnings.
        """
        payload = {
            'info': ['Converted!'],
            'warnings': [],
            'errors': [],
            'success': True,
            'message': 'All good'
        }
        mock_invoke.return_value = self.create_mock_payload(payload)
        mock_request_post.return_value = None

        self.tx_manager.start_job('job3')

        # job2's entry in database should have been updated
        job = TxJob(db_handler=self.tx_manager.job_db_handler).load({'job_id': 'job3'})
        self.assertEqual(job.job_id, 'job3')
        self.assertEqual(len(job.errors), 0)

    # noinspection PyUnusedLocal
    @mock.patch('libraries.aws_tools.lambda_handler.LambdaHandler.invoke')
    @mock.patch('requests.post')
    def test_start_job3(self, mock_request_post, mock_invoke):
        """
        Call start_job on job 3 from mock data.

        Invocation should result in an error

        :param mock_requests_post mock.MagicMock:
        :return:
        """
        payload = {
            'info': ['Conversion failed!'],
            'warnings': [],
            'errors': ['Some error'],
            'success': False,
            'message': 'Has errors, failed'
        }
        mock_invoke.return_value = self.create_mock_payload(payload)

        mock_request_post.return_value = None

        self.tx_manager.start_job('job4')

        # job3's entry in database should have been updated
        job = TxJob(db_handler=self.tx_manager.job_db_handler).load({'job_id': 'job4'})
        self.assertEqual(job.job_id, 'job4')
        self.assertTrue(len(job.errors) > 0)

    def test_start_job_failure(self):
        """Call start_job with non-runnable/non-existent jobs."""
        tx_manager = TxManager(**self.tx_manager_env_vars)
        ret0 = tx_manager.start_job('job1')
        ret4 = tx_manager.start_job('job5')
        ret5 = tx_manager.start_job('job6')

        self.assertEqual(ret0['job_id'], 'job1')
        self.assertEqual(ret4['job_id'], 'job5')
        self.assertEqual(ret5['job_id'], 'job6')
        self.assertFalse(ret5['success'])
        self.assertEqual(ret5['message'], 'No job with ID job6 has been requested')

        # last existent job (4) should be updated in database to include error
        # messages
        job = TxJob(db_handler=self.tx_manager.job_db_handler).load({'job_id': 'job5'})
        self.assertEqual(job.job_id, 'job5')
        self.assertTrue(len(job.errors) > 0)

    # noinspection PyUnusedLocal
    @mock.patch('libraries.aws_tools.lambda_handler.LambdaHandler.invoke')
    @mock.patch('requests.post')
    def test_start_job_bad_error(self, mock_requests_post, mock_invoke):
        """
        Call start_job in job 6 from mock data.

        Should fail due to the response having an errorMessage
        """
        job = TxJob(db_handler=self.tx_manager.job_db_handler).load({'job_id': 'job7'})
        error_to_check = 'something bad happened!'
        mock_invoke.return_value = {'errorMessage': 'Bad Request: {0}'.format(error_to_check)}
        mock_requests_post.return_value = None
        self.tx_manager.start_job('job7')
        # job 6's entry in database should have been updated
        job = TxJob(db_handler=self.tx_manager.job_db_handler).load({'job_id': 'job7'})
        self.assertEqual(job.job_id, 'job7')
        self.assertEqual(len(job.errors), 1)
        self.assertEqual(job.errors[0], error_to_check)

    # noinspection PyUnusedLocal
    @mock.patch('libraries.aws_tools.lambda_handler.LambdaHandler.invoke')
    @mock.patch('requests.post')
    def test_start_job_with_errors(self, mock_requests_post, mock_invoke):
        """
        Call start_job on job 7 from mock data.

        Invocation should result in an errors

        :param mock_requests_post mock.MagicMock:
        :return:
        """
        payload = {
            'info': ['Conversion failed!'],
            'warnings': [],
            'errors': ['Some error', 'another error'],
            'success': False,
            'message': 'Has errors, failed'
        }
        mock_invoke.return_value = self.create_mock_payload(payload)

        mock_requests_post.return_value = None

        self.tx_manager.start_job('job8')

        # job 7's entry in database should have been updated
        job = TxJob(db_handler=self.tx_manager.job_db_handler).load({'job_id': 'job8'})
        self.assertEqual(job.job_id, 'job8')
        self.assertEqual(len(job.errors), 2)

    def test_list_jobs(self):
        """Test list_jobs and list_endpoint methods."""
        tx_manager = TxManager(**self.tx_manager_env_vars)
        jobs = tx_manager.list_jobs({'gogs_user_token': 'token2'}, True)
        expected = [TxJob(self.job_items[job_id]).get_db_data() for job_id in self.job_items]
        self.assertItemsEqual(jobs, expected)

        self.assertRaises(Exception, tx_manager.list_jobs, {'bad_key': 'token1'})
        self.assertRaises(Exception, tx_manager.list_jobs, {'gogs_user_token': 'bad_token'})

        endpoints = tx_manager.list_endpoints()
        self.assertIsInstance(endpoints, dict)
        self.assertIn('version', endpoints)
        self.assertEqual(endpoints['version'], '1')
        self.assertIn('links', endpoints)
        self.assertIsInstance(endpoints['links'], list)
        for link_data in endpoints['links']:
            self.assertIsInstance(link_data, dict)
            self.assertIn('href', link_data)
            self.assertEqual(self.MOCK_API_URL + '/tx/job', link_data['href'])
            self.assertIn('rel', link_data)
            self.assertIsInstance(link_data['rel'], unicode)
            self.assertIn('method', link_data)
            self.assertIn(link_data['method'],
                          ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])

    def test_register_module(self):
        data = {
            'name': 'module1',
            'type': 'conversion',
            'resource_types': ['obs'],
            'input_format': 'md',
            'output_format': 'html'
        }
        self.tx_manager.register_module(data)
        tx_module = TxModule(db_handler=self.tx_manager.module_db_handler).load({'name': data['name']})
        data['public_links'] = ['{0}/tx/convert/{1}'.format(self.MOCK_API_URL, data['name'])]
        self.assertEqual(tx_module.get_db_data(), TxModule(data).get_db_data())

        test_missing_keys = ['name', 'type', 'input_format', 'output_format', 'resource_types']
        for key in test_missing_keys:
            # should raise an exception if data is missing a required field
            missing = data.copy()
            del missing[key]
            self.assertRaises(Exception, self.tx_manager.register_module, missing)

    def test_generate_dashboard(self):
        dashboard = self.tx_manager.generate_dashboard()
        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a status table tag
        status_table = soup.find('table', id='status')

        module_name = 'module1'
        expected_row_count = 12
        expected_success_count = 2
        expected_warning_count = 2
        expected_failure_count = 1
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count)

        module_name = 'module2'
        expected_row_count = 11
        expected_success_count = 2
        expected_warning_count = 0
        expected_failure_count = 2
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count)

        module_name = 'module3'
        expected_row_count = 9
        expected_success_count = 0
        expected_warning_count = 0
        expected_failure_count = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count)

        module_name = 'module4'
        expected_row_count = 0
        expected_success_count = 0
        expected_warning_count = 0
        expected_failure_count = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count)

        module_name = 'totals'
        expected_row_count = 5
        expected_success_count = 5
        expected_warning_count = 2
        expected_failure_count = 3
        expected_unregistered = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count, expected_unregistered)

        failure_table = soup.find('table', id='failed')
        expected_failure_count = 3
        self.validateFailureTable(failure_table, expected_failure_count)

    def test_generate_dashboard_max_two(self):
        expected_max_failures = 2
        dashboard = self.tx_manager.generate_dashboard(expected_max_failures)

        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a status table tag
        status_table = soup.find('table', id='status')

        module_name = 'module1'
        expected_row_count = 12
        expected_success_count = 2
        expected_warning_count = 2
        expected_failure_count = 1
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count)

        module_name = 'module2'
        expected_row_count = 11
        expected_success_count = 2
        expected_warning_count = 0
        expected_failure_count = 2
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count)

        module_name = 'module3'
        expected_row_count = 9
        expected_success_count = 0
        expected_warning_count = 0
        expected_failure_count = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count)

        module_name = 'totals'
        expected_row_count = 5
        expected_success_count = 5
        expected_warning_count = 2
        expected_failure_count = 3
        expected_unregistered = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                            expected_warning_count, expected_unregistered)

        failure_table = soup.find('table', id='failed')
        expected_failure_count = expected_max_failures
        self.validateFailureTable(failure_table, expected_failure_count)

    # helper methods #

    def create_mock_payload(self, payload):
        mock_payload = ManagerTest.PayloadMock()
        mock_payload.response = json.dumps(payload)
        mock_payload = {'Payload': mock_payload}
        return mock_payload

    def validateFailureTable(self, table, expectedFailureCount):
        self.assertIsNotNone(table)
        modules = table.findAll('tr', id=lambda x: x and x.startswith('failure-'))
        row_count = len(modules)
        self.assertEquals(row_count, expectedFailureCount)

    def validateModule(self, table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                       expected_warning_count, expected_unregistered=0):
        self.assertIsNotNone(table)
        modules = table.findAll('tr', id=lambda x: x and x.startswith(module_name + '-'))
        row_count = len(modules)
        self.assertEquals(row_count, expected_row_count)
        if expected_row_count > 0:
            success_count = self.getCountFromRow(table, module_name + '-job-success')
            self.assertEquals(success_count, expected_success_count)
            warning_count = self.getCountFromRow(table, module_name + '-job-warning')
            self.assertEquals(warning_count, expected_warning_count)
            failure_count = self.getCountFromRow(table, module_name + '-job-failure')
            self.assertEquals(failure_count, expected_failure_count)
            unregistered_count = self.getCountFromRow(table, module_name + '-job-unregistered')
            self.assertEquals(unregistered_count, expected_unregistered)
            expected_total_count = expected_failure_count + expected_success_count + expected_warning_count + expected_unregistered
            total_count = self.getCountFromRow(table, module_name + '-job-total')
            self.assertEquals(total_count, expected_total_count)

    def getCountFromRow(self, table, rowID):
        rows = table.findAll('tr', id=lambda x: x == rowID)
        if len(rows) == 0:
            return 0

        data_fields = rows[0].findAll('td')
        strings = data_fields[1].stripped_strings # get data from second column
        count = -1
        for string in strings:
            count = int(string)
            break

        return count

    def call_args(self, mock_object, num_args, num_kwargs=0):
        """
        :param mock_object: mock object that is expected to have been called
        :param num_args: expected number of (non-keyword) arguments
        :param num_kwargs: expected number of keyword arguments
        :return: (args, kwargs) of last invocation of mock_object
        """
        mock_object.assert_called()
        args, kwargs = mock_object.call_args
        self.assertEqual(len(args), num_args)
        self.assertEqual(len(kwargs), num_kwargs)
        return args, kwargs

    class PayloadMock(mock.Mock):
        response = None

        def read(self):
            return self.response

if __name__ == '__main__':
    unittest.main()
