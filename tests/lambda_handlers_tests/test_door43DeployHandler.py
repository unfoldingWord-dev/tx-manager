from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.door43_deploy_handler import Door43DeployHandler


class TestDoor43DeployerHandler(TestCase):

    @mock.patch('door43_tools.project_deployer.ProjectDeployer.redeploy_all_commits')
    @mock.patch('door43_tools.project_deployer.ProjectDeployer.deploy_revision_to_door43')
    def test_handle(self, mock_deploy_revision_to_door43, mock_redeploy_all_commits):
        mock_redeploy_all_commits.return_value = None
        mock_deploy_revision_to_door43.return_value = None

        # Test redeploy if a template change
        event = {
            'Records': [
                {
                    's3': {
                        'bucket': {
                            'name': 'test-my_bucket'
                        },
                        'object': {
                            'key': 'obs.html'
                        }
                    }
                }
            ]
        }
        handler = Door43DeployHandler()
        self.assertIsNone(handler.handle(event, None))

        # Test deploy if a build_log.json added
        event = {
            'Records': [
                {
                    's3': {
                        'bucket': {
                            'name': 'test-my_bucket'
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
