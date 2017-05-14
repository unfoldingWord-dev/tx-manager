from __future__ import absolute_import, unicode_literals, print_function
import itertools
import unittest
import mock
from bs4 import BeautifulSoup

from tests.manager_tests import mock_utils
from lambda_handlers.dashboard_handler import DashboardHandler


class DashboardHandlerTest(unittest.TestCase):
    MOCK_API_URL = "https://api.example.com"
    MOCK_CDN_URL = "https://cdn.example.com"
    MOCK_CALLBACK_URL = "https://callback.example.com/"
    MOCK_GOGS_URL = "https://mock.gogs.io"
    MOCK_CDN_BUCKET = 'mock_bucket'
    MOCK_JOB_TABLE_NAME = 'mock-job'
    MOCK_MODULE_TABLE_NAME = 'mock-module'

    mock_job_db = None
    mock_module_db = None
    mock_db = None
    mock_gogs = None

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
        """Create mock AWS handlers, and apply corresponding monkey patches."""
        cls.mock_job_db = mock_utils.mock_db_handler(data={
            "0": {
                "job_id": "0",
                "status": "started",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html",
                "convert_module": "module1",
                "errors" : []
            },
            "1": {
                "job_id": "1",
                "status": "requested",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html",
                "convert_module": "module1",
                "errors" : [ "error" ],
                "identifier" : "tx-manager-test-data/en-ulb-jud/6778aa89bd",
                "output" : "https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bd.zip",
                "created_at":	"2017-04-12T17:03:06Z"
            },
            "2": {
                "job_id": "2",
                "status": "requested",
                "resource_type": "ulb",
                "input_format": "usfm",
                "output_format": "html",
                "callback": DashboardHandlerTest.MOCK_CALLBACK_URL,
                "convert_module": "module1",
                "warnings" : []
            },
            "3": {
                "job_id": "3",
                "status": "requested",
                "resource_type": "other",
                "input_format": "md",
                "output_format": "html",
                "convert_module": "module1",
                "warnings" : [ "warning" ]
            },
            "4": {
                "job_id": "4",
                "status": "requested",
                "resource_type": "unsupported",
                "input_format": "md",
                "output_format": "html",
                "convert_module": "module1",
                "warnings" : [ "warning1", "warning2" ]
            },
            "6": {
                "job_id": "6",
                "status": "requested",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html",
                "convert_module": "module2"
            },
            "7": {
                "job_id": "7",
                "status": "requested",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html",
                "convert_module": "module2"
            },
            "8": {
                "job_id": "8",
                "status": "requested",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html",
                "convert_module": "module2",
                "identifier" : "tx-manager-test-data/en-ulb-jud/6778aa89bZ",
                "output" : "https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bdZ.zip",
                "errors" : [ "error1", "error2" ],
                "created_at":	"2017-03-12T17:03:076Z"
            },
            "9": {
                "job_id": "9",
                "status": "requested",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html",
                "convert_module": "module2",
                "identifier" : "tx-manager-test-data/en-ulb-jud/6778aa89bZZ",
                "output" : "https://test-cdn.door43.org/tx-manager-test-data/en-ulb-jud/6778aa89bdZZ.zip",
                "errors" : [ "error1","error2","error3" ],
                "created_at":	"2017-05-12T17:03:04Z"
            }
        }, keyname="job_id")
        cls.mock_module_db = mock_utils.mock_db_handler(data={
            "module1": {
                "name": "module1",
                "type": "conversion",
                "version": "1",
                "resource_types": ["obs", "ulb"],
                "input_format": "md",
                "output_format": "html",
                "public_links": ["{0}/tx/convert/md2html".format(cls.MOCK_API_URL)],
                "private_links": ["{0}/tx/private/module1".format(cls.MOCK_API_URL)],
                "options": {"pageSize": "A4"}
            },
            "module2": {
                "name": "module2",
                "type": "conversion",
                "version": "1",
                "resource_types": ["ulb"],
                "input_format": "usfm",
                "output_format": "html",
                "public_links": ["{0}/tx/convert/usfm2html".format(cls.MOCK_API_URL)],
                "private_links": [],
                "options": {"pageSize": "A4"}
            },
            "module3": {
                "name": "module3",
                "type": "conversion",
                "version": "1",
                "resource_types": ["other", "yet_another"],
                "input_format": "md",
                "output_format": "html",
                "public_links": [],
                "private_links": [],
                "options": {}
            }
        }, keyname="name")

        cls.mock_db = mock.MagicMock(
            side_effect=itertools.cycle([cls.mock_job_db, cls.mock_module_db]))
        cls.mock_gogs = mock.MagicMock(
            return_value=mock_utils.mock_gogs_handler(["token1", "token2"]))

        DashboardHandlerTest.patches = (
            mock.patch("manager.manager.DynamoDBHandler", cls.mock_db),
            mock.patch("manager.manager.GogsHandler", cls.mock_gogs),
        )

        for patch in DashboardHandlerTest.patches:
            patch.start()

    def setUp(self):
        DashboardHandlerTest.mock_job_db.reset_mock()
        DashboardHandlerTest.mock_module_db.reset_mock()
        DashboardHandlerTest.mock_db.reset_mock()
        DashboardHandlerTest.mock_gogs.reset_mock()
        DashboardHandlerTest.requested_urls = []

    @classmethod
    def tearDownClass(cls):
        for patch in DashboardHandlerTest.patches:
            patch.stop()

    def test_dashboard_handler_max_two(self):
        event = {
            "vars" : {
                'api_url': 'https://test-api.door43.org',
                'gogs_url': 'https://git.door43.org',
                'cdn_url': 'https://test-cdn.door43.org',
                'job_table_name': 'test-tx-job',
                'module_table_name': 'test-tx-module'
            },
            "api-gateway" : {
                "params" : {
                    'querystring': {
                        'failures': '2'
                    }
                }
            }
        }
        dashboard = DashboardHandler().handle(event, None)

        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a status table tag
        statusTable = soup.find('table', id="status")

        moduleName = 'module1'
        expectedRowCount = 12
        expectedSuccessCount = 2
        expectedWarningCount = 2
        expectedFailureCount = 1
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module2'
        expectedRowCount = 11
        expectedSuccessCount = 2
        expectedWarningCount = 0
        expectedFailureCount = 2
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module3'
        expectedRowCount = 9
        expectedSuccessCount = 0
        expectedWarningCount = 0
        expectedFailureCount = 0
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'totals'
        expectedRowCount = 4
        expectedSuccessCount = 4
        expectedWarningCount = 2
        expectedFailureCount = 3
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        failureTable = soup.find('table', id="failed")
        expectedFailureCount = 2
        self.validateTable( failureTable, expectedFailureCount)


    def test_dashboard_handler_no_failure_count(self):
        event = {
            "vars" : {
                'api_url': 'https://test-api.door43.org',
                'gogs_url': 'https://git.door43.org',
                'cdn_url': 'https://test-cdn.door43.org',
                'job_table_name': 'test-tx-job',
                'module_table_name': 'test-tx-module'
            }
        }
        dashboard = DashboardHandler().handle(event, None)

        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a status table tag
        statusTable = soup.find('table', id="status")

        moduleName = 'module1'
        expectedRowCount = 12
        expectedSuccessCount = 2
        expectedWarningCount = 2
        expectedFailureCount = 1
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module2'
        expectedRowCount = 11
        expectedSuccessCount = 2
        expectedWarningCount = 0
        expectedFailureCount = 2
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'module3'
        expectedRowCount = 9
        expectedSuccessCount = 0
        expectedWarningCount = 0
        expectedFailureCount = 0
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        moduleName = 'totals'
        expectedRowCount = 4
        expectedSuccessCount = 4
        expectedWarningCount = 2
        expectedFailureCount = 3
        self.validateModule(statusTable, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                            expectedWarningCount)

        failureTable = soup.find('table', id="failed")
        expectedFailureCount = 3
        self.validateTable( failureTable, expectedFailureCount)

    # helper methods #

    def validateTable(self, table, expectedFailureCount):
        self.assertIsNotNone(table)
        module = table.findAll('tr', id=lambda x: x and x.startswith('failure-'))
        rowCount = len(module)
        self.assertEquals(rowCount, expectedFailureCount)

    def validateModule(self, table, moduleName, expectedRowCount, expectedSuccessCount, expectedFailureCount,
                       expectedWarningCount):
        self.assertIsNotNone(table)
        module = table.findAll('tr', id=lambda x: x and x.startswith(moduleName + '-'))
        rowCount = len(module)
        self.assertEquals(rowCount, expectedRowCount)
        successCount = self.getCountFromRow(table, moduleName + '-job-success')
        self.assertEquals(successCount, expectedSuccessCount)
        warningCount = self.getCountFromRow(table, moduleName + '-job-warning')
        self.assertEquals(warningCount, expectedWarningCount)
        failureCount = self.getCountFromRow(table, moduleName + '-job-failure')
        self.assertEquals(failureCount, expectedFailureCount)
        expectedTotalCount = expectedFailureCount + expectedSuccessCount + expectedWarningCount
        totalCount = self.getCountFromRow(table, moduleName + '-job-total')
        self.assertEquals(totalCount, expectedTotalCount)

    def getCountFromRow(self, table, rowID):
        success = table.findAll('tr', id=lambda x: x == rowID)
        dataFields = success[0].findAll("td")
        strings = dataFields[1].stripped_strings # get data from second column
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

if __name__ == "__main__":
    unittest.main()
