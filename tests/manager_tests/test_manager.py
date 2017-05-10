from __future__ import absolute_import, unicode_literals, print_function
import itertools
import unittest
import mock
from six import StringIO
from bs4 import BeautifulSoup
from tests.manager_tests import mock_utils
from tests.manager_tests.mock_utils import MockResponse
from manager.job import TxJob
from manager.manager import TxManager
from manager.module import TxModule


class ManagerTest(unittest.TestCase):
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
                "output_format": "html"
            },
            "1": {
                "job_id": "1",
                "status": "requested",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html"
            },
            "2": {
                "job_id": "2",
                "status": "requested",
                "resource_type": "ulb",
                "input_format": "usfm",
                "output_format": "html",
                "callback": ManagerTest.MOCK_CALLBACK_URL,
            },
            "3": {
                "job_id": "3",
                "status": "requested",
                "resource_type": "other",
                "input_format": "md",
                "output_format": "html"
            },
            "4": {
                "job_id": "4",
                "status": "requested",
                "resource_type": "unsupported",
                "input_format": "md",
                "output_format": "html"
            },
            "6": {
                "job_id": "6",
                "status": "requested",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html"
            },
            "7": {
                "job_id": "7",
                "status": "requested",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "html"
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

        ManagerTest.patches = (
            mock.patch("manager.manager.DynamoDBHandler", cls.mock_db),
            mock.patch("manager.manager.GogsHandler", cls.mock_gogs),
        )

        for patch in ManagerTest.patches:
            patch.start()

    def setUp(self):
        ManagerTest.mock_job_db.reset_mock()
        ManagerTest.mock_module_db.reset_mock()
        ManagerTest.mock_db.reset_mock()
        ManagerTest.mock_gogs.reset_mock()
        ManagerTest.requested_urls = []

    @classmethod
    def tearDownClass(cls):
        for patch in ManagerTest.patches:
            patch.stop()

    def test_setup_job(self):
        """Successful call of setup_job."""
        tx_manager = TxManager(**self.tx_manager_env_vars)
        data = {
            "gogs_user_token": "token1",
            "cdn_bucket":  "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "obs",
            "input_format": "md",
            "output_format": "html"
        }
        tx_manager.setup_job(data)
        # assert an entry was aded to job database
        args, kwargs = self.call_args(ManagerTest.mock_job_db.insert_item, num_args=1)
        arg = args[0]
        self.assertIsInstance(arg, dict)
        self.assertEqual(arg["convert_module"], "module1")
        self.assertEqual(arg["resource_type"], "obs")
        self.assertEqual(arg["cdn_bucket"], "test_cdn_bucket")

    def test_setup_job_bad_requests(self):
        """Tests bad calls of setup_job due to missing or bad input."""
        tx_manager = TxManager(**self.tx_manager_env_vars)
        tx_manager.cdn_bucket = None

        # Missing gogs_user_token
        data = {
            "cdn_bucket":  "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "obs",
            "input_format": "md",
            "output_format": "html"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

        # Bad gogs_user_token
        data = {
            "gogs_user_token": "bad_token",
            "cdn_bucket":  "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "obs",
            "input_format": "md",
            "output_format": "html"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

        # Missing cdn_bucket
        data = {
            "gogs_user_token": "token1",
            "source": "test_source",
            "resource_type": "obs",
            "input_format": "md",
            "output_format": "html"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

        # Missing source
        data = {
            "gogs_user_token": "token1",
            "cdn_bucket":  "test_cdn_bucket",
            "resource_type": "obs",
            "input_format": "md",
            "output_format": "html"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

        # Missing resource_type
        tx_manager = TxManager(**self.tx_manager_env_vars)
        data = {
            "gogs_user_token": "token1",
            "cdn_bucket":  "test_cdn_bucket",
            "source": "test_source",
            "input_format": "md",
            "output_format": "html"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

        # Missing input_format
        data = {
            "gogs_user_token": "token1",
            "cdn_bucket":  "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "obs",
            "output_format": "html"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

        # Missing output_format
        data = {
            "gogs_user_token": "token1",
            "cdn_bucket":  "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "obs",
            "input_format": "md"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

    def test_setup_job_malformed_input(self):
        """Call setup_job with malformed data arguments."""
        tx_manager = TxManager()
        data = {
            "gogs_user_token": "token1",
            "cdn_bucket": "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "obs",
            "input_format": "md",
            "output_format": "html"
        }
        for key in data:
            # should raise an exception if data is missing a required field
            missing = data.copy()
            del missing[key]
            self.assertRaises(Exception, tx_manager.setup_job, missing)
        # should raise an exception if called with an invalid user_token
        bad_token = data.copy()
        bad_token["gogs_user_token"] = "bad_token"
        self.assertRaises(Exception, tx_manager.setup_job, bad_token)

    def test_setup_job_no_converter(self):
        """Call setup_job when there is no applicable converter."""
        tx_manager = TxManager(**self.tx_manager_env_vars)
        data = {
            "gogs_user_token": "token1",
            "cdn_bucket": "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "unrecognized_resource_type",
            "input_format": "md",
            "output_format": "html"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

    # noinspection PyUnusedLocal
    @mock.patch('requests.post')
    def test_start_job1(self, mock_requests_post):
        """
        Call start job in job 1 from mock data.

        Should be a successful invocation with warnings.
        """
        mock_requests_post.return_value = MockResponse({
            "info": ['Converted!'],
            "warnings": ['Missing something'],
            "errors": [],
            "success": True,
            "message": "Has some warnings"
        }, 200)

        tx_manager = TxManager(**self.tx_manager_env_vars)
        tx_manager.start_job("1")

        # job1's entry in database should have been updated
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIsInstance(keys, dict)
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], "1")
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("errors", data)
        self.assertEqual(len(data["errors"]), 0)
        self.assertIn("warnings", data)
        self.assertTrue(len(data["warnings"]) > 0)

    # noinspection PyUnusedLocal
    @mock.patch('requests.post')
    def test_start_job2(self, mock_requests_post):
        """
        Call start_job in job 2 from mock data.

        Should be a successful invocation without warnings.
        """
        mock_requests_post.return_value = MockResponse({
            "info": ['Converted!'],
            "warnings": [],
            "errors": [],
            "success": True,
            "message": "All good"
        }, 200)
        tx_manager = TxManager(**self.tx_manager_env_vars)
        tx_manager.start_job("2")

        # job2's entry in database should have been updated
        ManagerTest.mock_job_db.update_item.assert_called()
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIsInstance(keys, dict)
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], "2")
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("errors", data)
        self.assertEqual(len(data["errors"]), 0)

    # noinspection PyUnusedLocal
    @mock.patch('requests.post')
    def test_start_job3(self, mock_requests_post):
        """
        Call start_job on job 3 from mock data.

        Invocation should result in an error

        :param mock_requests_post mock.MagicMock:
        :return:
        """
        mock_requests_post.return_value = MockResponse({
            "info": ['Conversion failed!'],
            "warnings": [],
            "errors": ['Some error'],
            "success": False,
            "message": "Has errors, failed"
        }, 200)

        manager = TxManager(**self.tx_manager_env_vars)
        manager.start_job("3")

        # job3's entry in database should have been updated
        ManagerTest.mock_job_db.update_item.assert_called()
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], "3")
        self.assertIsInstance(keys, dict)
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("errors", data)
        self.assertTrue(len(data["errors"]) > 0)

    def test_start_job_failure(self):
        """Call start_job with non-runnable/non-existent jobs."""
        tx_manager = TxManager(**self.tx_manager_env_vars)
        ret0 = tx_manager.start_job("0")
        ret4 = tx_manager.start_job("4")
        ret5 = tx_manager.start_job("5")

        self.assertEqual(ret0['job_id'], "0")
        self.assertEqual(ret4['job_id'], "4")
        self.assertEqual(ret5['job_id'], "5")
        self.assertFalse(ret5['success'])
        self.assertEqual(ret5['message'], 'No job with ID 5 has been requested')

        # last existent job (4) should be updated in database to include error
        # messages
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIsInstance(keys, dict)
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], "4")
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("job_id", data)
        self.assertEqual(data["job_id"], "4")
        self.assertIn("errors", data)
        self.assertTrue(len(data["errors"]) > 0)

    # noinspection PyUnusedLocal
    @mock.patch('requests.post')
    def test_start_job_bad_error(self, mock_requests_post):
        """
        Call start_job in job 6 from mock data.

        Should fail due to the response having an errorMessage
        """
        error_to_check = "something bad happened!"
        mock_requests_post.return_value = MockResponse({"errorMessage": 'Bad Request: {0}'.format(error_to_check)}, 400)
        tx_manager = TxManager(**self.tx_manager_env_vars)
        tx_manager.start_job("6")
        # job 0's entry in database should have been updated
        ManagerTest.mock_job_db.update_item.assert_called()
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIsInstance(keys, dict)
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], "6")
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("errors", data)
        self.assertEqual(len(data["errors"]), 1)
        self.assertEqual(data["errors"][0], error_to_check)

    # noinspection PyUnusedLocal
    @mock.patch('requests.post')
    def test_start_job_with_errors(self, mock_requests_post):
        """
        Call start_job on job 7 from mock data.

        Invocation should result in an errors

        :param mock_requests_post mock.MagicMock:
        :return:
        """
        mock_requests_post.return_value = MockResponse({
            "info": ['Conversion failed!'],
            "warnings": [],
            "errors": ['Some error', 'another error'],
            "success": False,
            "message": "Has errors, failed"
        }, 200)

        manager = TxManager(**self.tx_manager_env_vars)
        manager.start_job("7")

        # job 7's entry in database should have been updated
        ManagerTest.mock_job_db.update_item.assert_called()
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], "7")
        self.assertIsInstance(keys, dict)
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("errors", data)
        self.assertEqual(len(data["errors"]), 2)

    def test_list_jobs(self):
        """Test list_jobs and list_endpoint methods."""
        tx_manager = TxManager(**self.tx_manager_env_vars)
        jobs = tx_manager.list_jobs({"gogs_user_token": "token2"}, True)
        expected = [TxJob(job).get_db_data()
                    for job in ManagerTest.mock_job_db.mock_data.values()]
        self.assertEqual(jobs, expected)

        self.assertRaises(Exception, tx_manager.list_jobs, {"bad_key": "token1"})
        self.assertRaises(Exception, tx_manager.list_jobs, {"gogs_user_token": "bad_token"})

        endpoints = tx_manager.list_endpoints()
        self.assertIsInstance(endpoints, dict)
        self.assertIn("version", endpoints)
        self.assertEqual(endpoints["version"], "1")
        self.assertIn("links", endpoints)
        self.assertIsInstance(endpoints["links"], list)
        for link_data in endpoints["links"]:
            self.assertIsInstance(link_data, dict)
            self.assertIn("href", link_data)
            self.assertEqual(self.MOCK_API_URL + "/tx/job", link_data["href"])
            self.assertIn("rel", link_data)
            self.assertIsInstance(link_data["rel"], unicode)
            self.assertIn("method", link_data)
            self.assertIn(link_data["method"],
                          ["GET", "POST", "PUT", "PATCH", "DELETE"])

    def test_register_module(self):
        manager = TxManager(**self.tx_manager_env_vars)

        data = {
            "name": "module1",
            "type": "conversion",
            "resource_types": ["obs"],
            "input_format": "md",
            "output_format": "html"
        }
        manager.register_module(data)
        ManagerTest.mock_module_db.insert_item.assert_called()
        args, kwargs = self.call_args(ManagerTest.mock_module_db.insert_item, num_args=1)
        data['public_links'] = ['{0}/tx/convert/{1}'.format(self.MOCK_API_URL, data['name'])]
        self.assertEqual(args[0], TxModule(data).get_db_data())

        test_missing_keys = ['name', 'type', 'input_format', 'output_format', 'resource_types']
        for key in test_missing_keys:
            # should raise an exception if data is missing a required field
            missing = data.copy()
            del missing[key]
            self.assertRaises(Exception, manager.register_module, missing)

    def test_debug_print(self):
        for quiet in (True, False):
            manager = TxManager(quiet=quiet)
            mock_stdout = StringIO()
            with mock.patch("sys.stdout", mock_stdout):
                manager.debug_print("Hello world")
                if quiet:
                    self.assertEqual(mock_stdout.getvalue(), "")
                else:
                    self.assertEqual(mock_stdout.getvalue(), "Hello world\n")

    def test_get_update_delete_job(self):
        """Test [get/update/delete]_job methods."""
        manager = TxManager(**self.tx_manager_env_vars)

        # get_job
        job = manager.get_job("0")
        self.assertIsInstance(job, TxJob)
        self.assertEqual(job.job_id, "0")
        self.assertEqual(job.status, "started")

        # update_job
        manager.update_job(job)
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item,
                                      num_args=2)
        self.assertEqual(args[0], {"job_id": "0"})
        self.assertEqual(args[1], job.get_db_data())

        # delete_job
        manager.delete_job(job)
        args, kwargs = self.call_args(ManagerTest.mock_job_db.delete_item,
                                      num_args=1)
        self.assertEqual(args[0], {"job_id": "0"})

    def test_get_update_delete_module(self):
        """Test [get/update/delete]_module methods."""
        manager = TxManager(**self.tx_manager_env_vars)

        # get_module
        module = manager.get_module("module1")
        self.assertIsInstance(module, TxModule)
        self.assertEqual(module.name, "module1")
        self.assertEqual(module.input_format, "md")

        # update_module
        manager.update_module(module)
        args, kwargs = self.call_args(ManagerTest.mock_module_db.update_item,
                                      num_args=2)
        self.assertEqual(args[0], {"name": "module1"})
        self.assertEqual(args[1], module.get_db_data())

        # delete_module
        manager.delete_module(module)
        args, kwargs = self.call_args(ManagerTest.mock_module_db.delete_item,
                                      num_args=1)
        self.assertEqual(args[0], {"name": "module1"})

    def test_generate_dashboard(self):
        manager = TxManager()
        dashboard = manager.generate_dashboard()
        # the title should be tX-Manager Dashboard
        self.assertEqual(dashboard['title'], 'tX-Manager Dashboard')
        soup = BeautifulSoup(dashboard['body'], 'html.parser')
        # there should be a table tag
        self.assertIsNotNone(soup.find('table'))
        module1 = soup.table.findAll('tr', id=lambda x: x and x.startswith('module1-'))
        self.assertEquals(len(module1), 12) # module1 should have 12 rows of info
        module2 = soup.table.findAll('tr', id=lambda x: x and x.startswith('module2-'))
        self.assertEquals(len(module2), 11)  # module2 should have 11 rows of info
        module3 = soup.table.findAll('tr', id=lambda x: x and x.startswith('module3-'))
        self.assertEquals(len(module3), 9) # module3 should have 9 rows of info

    # helper methods #

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
