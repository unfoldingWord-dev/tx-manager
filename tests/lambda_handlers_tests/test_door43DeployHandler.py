from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.door43_deploy_handler import Door43DeployHandler


class TestDoor43DeployerHandler(TestCase):

    def setUp(self):
        """Runs before each test."""
        self.returned_key = None

    @mock.patch('libraries.door43_tools.project_deployer.ProjectDeployer.deploy_revision_to_door43')
    def test_deploy_record(self, mock_deploy_revision_to_door43):
        mock_deploy_revision_to_door43.return_value = None

        # Test deploy if a build_log.json added
        event = {
            'Records': [
                {
                    's3': {
                        'bucket': {
                            'name': 'test-cdn.door43.org'
                        },
                        'object': {
                            'key': 'build_log.json'
                        }
                    }
                },
            ]
        }
        handler = Door43DeployHandler()
        self.assertIsNone(handler.handle(event, None))

    @mock.patch('libraries.door43_tools.project_deployer.ProjectDeployer.deploy_revision_to_door43')
    def test_deploy_build_log_key(self, mock_deploy_revision_to_door43):
        mock_deploy_revision_to_door43.return_value = None

        # Test deploy if a build_log.json added
        event = {
            'prefix': "dev-",
            'build_log_key': "dummy_key",
        }
        handler = Door43DeployHandler()
        self.assertIsNone(handler.handle(event, None))

    @mock.patch('libraries.door43_tools.project_deployer.ProjectDeployer.redeploy_all_projects')
    def test_redeploy_all(self, mock_redeploy_all_projects):
        # given
        mock_redeploy_all_projects.side_effect = self.mock_redeploy_all_projects
        expected_key = 'tx_door43_deploy'
        handler = Door43DeployHandler()

        # when
        # Test redeploy all projects
        results = handler.handle({'cdn_bucket': 'test-cdn.door43.org'}, None)

        # then
        self.assertEquals(self.returned_key, expected_key)

    @mock.patch('libraries.door43_tools.project_deployer.ProjectDeployer.redeploy_all_projects')
    def test_redeploy_all_exception(self, mock_redeploy_all_projects):
        # given
        mock_redeploy_all_projects.side_effect = self.mock_redeploy_all_projects_exception
        expected_key = 'tx_door43_deploy'
        handler = Door43DeployHandler()

        # when
        # Test redeploy all projects
        results = handler.handle({'cdn_bucket': 'test-cdn.door43.org'}, None)

        # then
        self.assertEquals(self.returned_key, expected_key)

    #
    # helpers
    #

    def mock_redeploy_all_projects(self, key):
        self.returned_key = key

    def mock_redeploy_all_projects_exception(self, key):
        self.returned_key = key
        raise NotImplementedError("Test Exception")
