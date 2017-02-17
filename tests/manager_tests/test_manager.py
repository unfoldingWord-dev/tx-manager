from __future__ import absolute_import, unicode_literals, print_function
import itertools
import unittest
import mock
import responses
from six import StringIO
from tests.manager_tests import mock_utils
from manager.job import TxJob
from manager.manager import TxManager
from manager.module import TxModule


class ManagerTest(unittest.TestCase):
    MOCK_API_URL = "https://api.example.com"
    MOCK_CALLBACK_URL = "https://callback.example.com/"
    MOCK_GOGS_URL = "https://mock.gogs.io"

    mock_job_db = None
    mock_module_db = None
    mock_db = None
    mock_gogs = None
    mock_lambda = None

    patches = []

    @classmethod
    def setUpClass(cls):
        """
        Create mock AWS handlers, and apply corresponding monkey patches
        """
        cls.mock_job_db = mock_utils.mock_db_handler(data={
            0: {
                "job_id": 0,
                "status": "started",
                "resource_type": "obs",
                "input_format": "markdown",
                "output_format": "html"
            },
            1: {
                "job_id": 1,
                "status": "requested",
                "resource_type": "obs",
                "input_format": "markdown",
                "output_format": "html"
            },
            2: {
                "job_id": 2,
                "status": "requested",
                "resource_type": "ulb",
                "input_format": "usfm",
                "output_format": "html",
                "callback": ManagerTest.MOCK_CALLBACK_URL,
            },
            3: {
                "job_id": 3,
                "status": "requested",
                "resource_type": "other",
                "input_format": "markdown",
                "output_format": "html"
            },
            4: {
                "job_id": 4,
                "status": "requested",
                "resource_type": "unsupported",
                "input_format": "markdown",
                "output_format": "html"
            }
        }, keyname="job_id")
        cls.mock_module_db = mock_utils.mock_db_handler(data={
            "module1": {
                "name": "module1",
                "resource_types": ["obs", "ulb"],
                "input_format": "markdown",
                "output_format": "html"
            },
            "module2": {
                "name": "module2",
                "resource_types": ["ulb"],
                "input_format": "usfm",
                "output_format": "html"
            },
            "module3": {
                "name": "module3",
                "resource_types": ["other", "yet_another"],
                "input_format": "markdown",
                "output_format": "html"
            }
        }, keyname="name")

        cls.mock_db = mock.MagicMock(
            side_effect=itertools.cycle([cls.mock_job_db, cls.mock_module_db]))
        cls.mock_gogs = mock.MagicMock(
            return_value=mock_utils.mock_gogs_handler(["token1", "token2"]))
        cls.mock_lambda = mock.MagicMock(
            return_value=mock_utils.mock_lambda_handler(["module2"], ["module1"]))

        ManagerTest.patches = (
            mock.patch("manager.manager.DynamoDBHandler", cls.mock_db),
            mock.patch("manager.manager.GogsHandler", cls.mock_gogs),
            mock.patch("manager.manager.LambdaHandler", cls.mock_lambda)
        )

        for patch in ManagerTest.patches:
            patch.start()

    def setUp(self):
        ManagerTest.mock_job_db.reset_mock()
        ManagerTest.mock_module_db.reset_mock()
        ManagerTest.mock_db.reset_mock()
        ManagerTest.mock_gogs.reset_mock()
        ManagerTest.mock_lambda.reset_mock()

    @classmethod
    def tearDownClass(cls):
        for patch in ManagerTest.patches:
            patch.stop()

    def test_setup_job(self):
        """
        Successful call of setup_job
        """
        tx_manager = TxManager(gogs_url=self.MOCK_GOGS_URL)
        data = {
            "user_token": "token1",
            "cdn_bucket":  "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "obs",
            "input_format": "markdown",
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

    def test_setup_job_malformed_input(self):
        """
        Call setup_job with malformed data arguments
        """
        tx_manager = TxManager()
        data = {
            "user_token": "token1",
            "cdn_bucket": "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "obs",
            "input_format": "markdown",
            "output_format": "html"
        }
        for key in data:
            # should raise an exception if data is missing a required field
            missing = data.copy()
            del missing[key]
            self.assertRaises(Exception, tx_manager.setup_job, missing)
        # should raise an exception if called with an invalid user_token
        bad_token = data.copy()
        bad_token["user_token"] = "bad_token"
        self.assertRaises(Exception, tx_manager.setup_job, bad_token)

    def test_setup_job_no_converter(self):
        """
        Call setup_job when there is no applicable converter.
        """
        tx_manager = TxManager()
        data = {
            "user_token": "token1",
            "cdn_bucket": "test_cdn_bucket",
            "source": "test_source",
            "resource_type": "unrecognized_resource_type",
            "input_format": "markdown",
            "output_format": "html"
        }
        self.assertRaises(Exception, tx_manager.setup_job, data)

    def test_start_job1(self):
        """
        Call start job in job 1 from mock data. Should be a successful
        invocation with warnings.
        """
        tx_manager = TxManager()
        tx_manager.start_job(1)
        # assert that correct lambda function was invoked
        args, kwargs = self.call_args(ManagerTest.mock_lambda().invoke, num_args=2)
        module_name = args[0]
        self.assertEqual(module_name, "module1")
        payload = args[1]
        self.assertIsInstance(payload, dict)
        self.assertIn("data", payload)
        self.assertIn("job", payload["data"])

        # job1's entry in database should have been updated
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIsInstance(keys, dict)
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], 1)
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("errors", data)
        self.assertEqual(len(data["errors"]), 0)
        self.assertIn("warnings", data)
        self.assertTrue(len(data["warnings"]) > 0)

    @responses.activate
    def test_start_job2(self):
        """
        Call start_job in job 2 from mock data. Should be a successful
        invocation without warnings.
        """
        # mock out job 2's callback
        responses.add(responses.POST, ManagerTest.MOCK_CALLBACK_URL)
        tx_manager = TxManager()
        tx_manager.start_job(2)
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(responses.calls[0].request.url, ManagerTest.MOCK_CALLBACK_URL)
        # assert that correct lambda function was invoked
        args, kwargs = self.call_args(ManagerTest.mock_lambda().invoke, num_args=2)
        module_name = args[0]
        self.assertEqual(module_name, "module2")
        payload = args[1]
        self.assertIsInstance(payload, dict)
        self.assertIn("data", payload)
        self.assertIn("job", payload["data"])

        # job2's entry in database should have been updated
        ManagerTest.mock_job_db.update_item.assert_called()
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIsInstance(keys, dict)
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], 2)
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("errors", data)
        self.assertEqual(len(data["errors"]), 0)

    def test_start_job3(self):
        """
        Call start_job on job 3 from mock data. Invocation should result in an error
        """
        manager = TxManager()
        manager.start_job(3)
        ManagerTest.mock_lambda().invoke.assert_called()
        # assert that correct lambda function was invoked
        args, kwargs = self.call_args(ManagerTest.mock_lambda().invoke, num_args=2)
        module_name = args[0]
        self.assertEqual(module_name, "module3")
        payload = args[1]
        self.assertIsInstance(payload, dict)
        self.assertIn("data", payload)
        self.assertIn("job", payload["data"])

        # job3's entry in database should have been updated
        ManagerTest.mock_job_db.update_item.assert_called()
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], 3)
        self.assertIsInstance(keys, dict)
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("errors", data)
        self.assertTrue(len(data["errors"]) > 0)

    def test_start_job_failure(self):
        """
        Call start_job with non-runnable/non-existent jobs
        """
        tx_manager = TxManager()
        tx_manager.start_job(0)
        tx_manager.start_job(4)
        tx_manager.start_job(5)

        # no lambda function should have been invoked
        ManagerTest.mock_lambda().invoke.assert_not_called()

        # last existent job (4) should be updated in database to include error
        # messages
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item, num_args=2)
        keys = args[0]
        self.assertIsInstance(keys, dict)
        self.assertIn("job_id", keys)
        self.assertEqual(keys["job_id"], 4)
        data = args[1]
        self.assertIsInstance(data, dict)
        self.assertIn("job_id", data)
        self.assertEqual(data["job_id"], 4)
        self.assertIn("errors", data)
        self.assertTrue(len(data["errors"]) > 0)

    def test_list(self):
        """
        Test list_jobs and list_endpoint methods
        """
        tx_manager = TxManager(api_url=self.MOCK_API_URL, gogs_url=self.MOCK_GOGS_URL)
        jobs = tx_manager.list_jobs({"user_token": "token2"}, True)
        expected = [TxJob(job).get_db_data()
                    for job in ManagerTest.mock_job_db.mock_data.values()]
        self.assertEqual(jobs, expected)

        self.assertRaises(Exception, tx_manager.list_jobs, {"bad_key": "token1"})
        self.assertRaises(Exception, tx_manager.list_jobs, {"user_token": "bad_token"})

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
            self.assertIsInstance(link_data["rel"], str)
            self.assertIn("method", link_data)
            self.assertIn(link_data["method"],
                          ["GET", "POST", "PUT", "PATCH", "DELETE"])

    def test_register_module(self):
        manager = TxManager()

        data = {
            "name": "module1",
            "type": "conversion",
            "resource_types": ["obs"],
            "input_format": "markdown",
            "output_format": "html"
        }
        manager.register_module(data)
        ManagerTest.mock_module_db.insert_item.assert_called()
        args, kwargs = self.call_args(ManagerTest.mock_module_db.insert_item, num_args=1)
        self.assertEqual(args[0], TxModule(data).get_db_data())

        for key in data:
            # should raise an expection if data is missing a required field
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
        """
        Test [get/update/delete]_job methods
        """
        manager = TxManager()

        # get_job
        job = manager.get_job(0)
        self.assertIsInstance(job, TxJob)
        self.assertEqual(job.job_id, 0)
        self.assertEqual(job.status, "started")

        # update_job
        manager.update_job(job)
        args, kwargs = self.call_args(ManagerTest.mock_job_db.update_item,
                                      num_args=2)
        self.assertEqual(args[0], {"job_id": 0})
        self.assertEqual(args[1], job.get_db_data())

        # delete_job
        manager.delete_job(job)
        args, kwargs = self.call_args(ManagerTest.mock_job_db.delete_item,
                                      num_args=1)
        self.assertEqual(args[0], {"job_id": 0})

    def test_get_update_delete_module(self):
        """
        Test [get/update/delete]_module methods
        """
        manager = TxManager()

        # get_module
        module = manager.get_module("module1")
        self.assertIsInstance(module, TxModule)
        self.assertEqual(module.name, "module1")
        self.assertEqual(module.input_format, "markdown")

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
