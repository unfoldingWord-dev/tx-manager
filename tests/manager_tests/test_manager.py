from __future__ import absolute_import, unicode_literals, print_function
import json
import unittest
import mock
from bs4 import BeautifulSoup
from tests.manager_tests import mock_utils
from moto import mock_dynamodb2
from datetime import datetime
from libraries.models.job import TxJob
from libraries.manager.manager import TxManager
from libraries.models.module import TxModule
from libraries.app.app import App


@mock_dynamodb2
class ManagerTest(unittest.TestCase):
    MOCK_CALLBACK_URL = 'http://example.com/client/callback'

    requested_urls = []
    mock_gogs = None

    @classmethod
    def setUpClass(cls):
        cls.mock_gogs = mock_utils.mock_gogs_handler(['token1', 'token2'])
        ManagerTest.patches = (
            mock.patch('libraries.app.app.GogsHandler', cls.mock_gogs),
        )
        for patch in ManagerTest.patches:
            patch.start()

    @classmethod
    def tearDownClass(cls):
        for patch in ManagerTest.patches:
            patch.stop()

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        App._gogs_handler = ManagerTest.mock_gogs
        ManagerTest.mock_gogs.reset_mock()
        ManagerTest.requested_urls = []
        self.tx_manager = TxManager()
        self.job_items = {}
        self.module_items = {}
        self.init_items()
        self.populate_tables()

    def tearDown(self):
        """Runs after each test."""
        App.db_close()

    def init_items(self):
        self.job_items = {
            'job1': {
                'job_id': 'job1',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'errors': [],
                'identifier': 'dummy-repo/dummy-user/dummy-commit',
                'cdn_bucket': 'cdn.door43.org',
                'source': 'https://door43.org/dummy_source',
                'output': 'https://door43.org/dummy_output',
                'manifests_id': 1
            },
            'job2': {
                'job_id': 'job2',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'cdn_bucket': 'cdn.door43.org',
                'identifier': 'tx-manager-test-data/en-ulb-jud/6778aa89bd',
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bd.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750d.zip',
                'manifests_id': 2
            },
            'job3': {
                'job_id': 'job3',
                'status': 'requested',
                'resource_type': 'ulb',
                'input_format': 'usfm',
                'output_format': 'html',
                'callback': ManagerTest.MOCK_CALLBACK_URL,
                'convert_module': 'module1',
                'identifier': 'dummy-repo/dummy-user/dummy-commit',
                'cdn_bucket': 'cdn.door43.org',
                'source': 'https://door43.org/dummy_source',
                'output': 'https://door43.org/dummy_output',
                'warnings': [],
                'manifests_id': 3
            },
            'job4': {
                'job_id': 'job4',
                'status': 'requested',
                'resource_type': 'other',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'identifier': 'dummy-repo/dummy-user/dummy-commit',
                'cdn_bucket': 'cdn.door43.org',
                'source': 'https://door43.org/dummy_source',
                'output': 'https://door43.org/dummy_output',
                'manifests_id': 4
            },
            'job5': {
                'job_id': 'job5',
                'status': 'requested',
                'resource_type': 'unsupported',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module1',
                'identifier': 'dummy-repo/dummy-user/dummy-commit',
                'cdn_bucket': 'cdn.door43.org',
                'source': 'https://door43.org/dummy_source',
                'output': 'https://door43.org/dummy_output',
                'manifests_id': 5
            },
            'job7': {
                'job_id': 'job7',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module2',
                'identifier': 'dummy-repo/dummy-user/dummy-commit',
                'cdn_bucket': 'cdn.door43.org',
                'source': 'https://door43.org/dummy_source',
                'output': 'https://door43.org/dummy_output',
                'manifests_id': 7
            },
            'job8': {
                'job_id': 'job8',
                'status': 'success',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module2',
                'identifier': 'dummy-repo/dummy-user/dummy-commit',
                'cdn_bucket': 'cdn.door43.org',
                'source': 'https://door43.org/dummy_source',
                'output': 'https://door43.org/dummy_output',
                'manifests_id': 8
            },
            'job9': {
                'job_id': 'job9',
                'status': 'requested',
                'resource_type': 'obs',
                'input_format': 'html',
                'output_format': 'pdf',
                'convert_module': 'module4',
                'identifier': 'dummy-repo/dummy-user/dummy-commit',
                'cdn_bucket': 'cdn.door43.org',
                'source': 'https://door43.org/dummy_source',
                'output': 'https://door43.org/dummy_output',
                'manifests_id': 9
            },
            'job10': {
                'job_id': 'job10',
                'status': 'failed',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module2',
                'identifier': 'tx-manager-test-data/en-ulb-jud/6778aa89bZ',
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bdZ.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750dZ.zip',
                'errors': ['error1', 'error2'],
                'cdn_bucket': 'cdn.door43.org',
                'manifests_id': 10
            },
            'job11': {
                'job_id': 'job11',
                'status': 'warnings',
                'resource_type': 'obs',
                'input_format': 'md',
                'output_format': 'html',
                'convert_module': 'module2',
                'identifier': 'tx-manager-test-data/en-ulb-jud/6778aa89bZZ',
                'output': 'https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bdZZ.zip',
                'source': 'https://s3-us-west-2.amazonaws.com/tx-webhook-client/preconvert/e8eb91750dZZ.zip',
                'errors': ['error1', 'error2', 'error3'],
                'cdn_bucket': 'cdn.door43.org',
                'manifests_id': 11
            }
        }
        self.module_items = {
            'module1': {
                'name': 'module1',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['obs', 'ulb'],
                'input_format': ['md'],
                'output_format': ['html'],
                'public_links': ['{0}/tx/convert/md2html'.format(App.api_url)],
                'private_links': ['{0}/tx/private/module1'.format(App.api_url)],
                'options': {'pageSize': 'A4'}
            },
            'module2': {
                'name': 'module2',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['ulb'],
                'input_format': ['usfm'],
                'output_format': ['html'],
                'public_links': ['{0}/tx/convert/usfm2html'.format(App.api_url)],
                'private_links': [],
                'options': {'pageSize': 'A4'}
            },
            'module3': {
                'name': 'module3',
                'type': 'conversion',
                'version': '1',
                'resource_types': ['other', 'yet_another'],
                'input_format': ['md'],
                'output_format': ['html'],
                'public_links': [],
                'private_links': [],
                'options': {}
            }
        }

    def populate_tables(self):
        for idx in self.job_items:
            tx_job = TxJob(**self.job_items[idx])
            tx_job.insert()

        for idx in self.module_items:
            tx_module = TxModule(**self.module_items[idx])
            tx_module.insert()

    def test_list_jobs(self):
        """Test list_jobs and list_endpoint methods."""
        tx_manager = TxManager()
        jobs = tx_manager.list_jobs({'gogs_user_token': 'token2'}, True)
        self.assertEqual(jobs.count(), len(self.job_items))

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
            self.assertEqual(App.api_url + '/tx/job', link_data['href'])
            self.assertIn('rel', link_data)
            self.assertIsInstance(link_data['rel'], unicode)
            self.assertIn('method', link_data)
            self.assertIn(link_data['method'],
                          ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])

    def test_register_module(self):
        data = {
            'name': 'module4',
            'type': 'conversion',
            'resource_types': ['obs'],
            'input_format': 'md',
            'output_format': 'html',
            'options': {'pageSize': 'A4'},
            'public_links': [],
            'private_links': []
        }
        self.tx_manager.register_module(data)
        tx_module = TxModule.get(name=data['name'])
        self.assertIsNotNone(tx_module)
        self.assertEqual(tx_module.options['pageSize'], 'A4')
        self.assertEqual(tx_module.created_at.year, datetime.utcnow().year)
        self.assertEqual(tx_module.updated_at.year, datetime.utcnow().year)
        self.assertEqual(tx_module.public_links, ['{0}/tx/convert/{1}'.format(App.api_url, data['name'])])

        test_missing_keys = ['name', 'type', 'input_format', 'resource_types']
        for key in test_missing_keys:
            # should raise an exception if data is missing a required field
            missing = data.copy()
            del missing[key]
            self.assertRaises(Exception, self.tx_manager.register_module, missing)

    def test_generate_dashboard(self):
        self.tx_manager.build_language_popularity_tables = self.mock_build_language_popularity_tables
        dashboard = self.tx_manager.generate_dashboard()
        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        self.assertFalse('html.parser' in dashboard['body'])
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a status table tag
        status_table = soup.find('table', id='status')

        module_name = 'module1'
        expected_row_count = 12
        expected_success_count = 0
        expected_warning_count = 0
        expected_failure_count = 5
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, 
                            expected_failure_count, expected_warning_count)

        module_name = 'module2'
        expected_row_count = 11
        expected_success_count = 1
        expected_warning_count = 1
        expected_failure_count = 2
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count,
                            expected_failure_count, expected_warning_count)

        module_name = 'module3'
        expected_row_count = 9
        expected_success_count = 0
        expected_warning_count = 0
        expected_failure_count = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, 
                            expected_failure_count, expected_warning_count)

        module_name = 'module4'
        expected_row_count = 0
        expected_success_count = 0
        expected_warning_count = 0
        expected_failure_count = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, 
                            expected_failure_count, expected_warning_count)

        module_name = 'totals'
        expected_row_count = 5
        expected_success_count = 1
        expected_warning_count = 1
        expected_failure_count = 8
        expected_unregistered = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count, 
                            expected_failure_count, expected_warning_count, expected_unregistered)

        failure_table = soup.find('table', id='failed')
        expected_failure_count = 8
        self.validateFailureTable(failure_table, expected_failure_count)

    def test_generate_dashboard_max_two(self):
        expected_max_failures = 2
        self.tx_manager.build_language_popularity_tables = self.mock_build_language_popularity_tables
        dashboard = self.tx_manager.generate_dashboard(expected_max_failures)

        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a status table tag
        status_table = soup.find('table', id='status')

        module_name = 'module1'
        expected_row_count = 12
        expected_success_count = 0
        expected_warning_count = 0
        expected_failure_count = 5
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count,
                            expected_failure_count, expected_warning_count)

        module_name = 'module2'
        expected_row_count = 11
        expected_success_count = 1
        expected_warning_count = 1
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
        expected_success_count = 1
        expected_warning_count = 1
        expected_failure_count = 8
        expected_unregistered = 0
        self.validateModule(status_table, module_name, expected_row_count, expected_success_count,
                            expected_failure_count, expected_warning_count, expected_unregistered)

        failure_table = soup.find('table', id='failed')
        expected_failure_count = expected_max_failures
        self.validateFailureTable(failure_table, expected_failure_count)

    # helper methods #

    def create_mock_payload(self, payload):
        mock_payload = ManagerTest.PayloadMock()
        mock_payload.response = json.dumps(payload)
        mock_payload = {'Payload': mock_payload}
        return mock_payload

    def validateFailureTable(self, table, expected_failure_count):
        self.assertIsNotNone(table)
        modules = table.findAll('tr', id=lambda x: x and x.startswith('failure-'))
        row_count = len(modules)
        self.assertEquals(row_count, expected_failure_count)

    def validateModule(self, table, module_name, expected_row_count, expected_success_count, expected_failure_count,
                       expected_warning_count, expected_unregistered=0):
        self.assertIsNotNone(table)
        modules = table.findAll('tr', id=lambda x: x and x.startswith(module_name + '-'))
        row_count = len(modules)
        self.assertEquals(row_count, expected_row_count)
        if expected_row_count > 0:
            success_count = self.get_count_from_row(table, module_name + '-job-success')
            self.assertEquals(success_count, expected_success_count)
            warning_count = self.get_count_from_row(table, module_name + '-job-warning')
            self.assertEquals(warning_count, expected_warning_count)
            failure_count = self.get_count_from_row(table, module_name + '-job-failure')
            self.assertEquals(failure_count, expected_failure_count)
            unregistered_count = self.get_count_from_row(table, module_name + '-job-unregistered')
            self.assertEquals(unregistered_count, expected_unregistered)
            expected_total_count = expected_failure_count + expected_success_count + expected_warning_count + expected_unregistered
            total_count = self.get_count_from_row(table, module_name + '-job-total')
            self.assertEquals(total_count, expected_total_count)

    def get_count_from_row(self, table, rowID):
        rows = table.findAll('tr', id=lambda x: x == rowID)
        if len(rows) == 0:
            return 0

        data_fields = rows[0].findAll('td')
        strings = data_fields[1].stripped_strings  # get data from second column
        count = -1
        for string in strings:
            count = int(string)
            break

        return count

    def mock_build_language_popularity_tables(self, body, max_count):
        pass

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
