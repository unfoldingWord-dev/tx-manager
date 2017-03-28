from __future__ import absolute_import, unicode_literals, print_function
import unittest
import os
from moto import mock_s3
from door43_tools.project_deployer import ProjectDeployer


@mock_s3
class ProjectDeployerTests(unittest.TestCase):
    MOCK_CDN_BUCKET = "test_cdn"
    MOCK_DOOR43_BUCKET = "test_door43"

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        self.setup_s3_for_deployer()

    def test_obs_deploy_revision_to_door43(self):
        build_log_key = '{0}/build_log.json'.format(self.project_key)
        ret = self.deployer.deploy_revision_to_door43(build_log_key)
        self.assertTrue(ret)

    def test_bad_deploy_revision_to_door43(self):
        bad_key = 'u/test_user/test_repo/12345678/bad_build_log.json'
        ret = self.deployer.deploy_revision_to_door43(bad_key)
        self.assertFalse(ret)

    def setup_s3_for_deployer(self):
        self.deployer = ProjectDeployer(self.MOCK_CDN_BUCKET, self.MOCK_DOOR43_BUCKET)
        self.project_dir = os.path.join(self.resources_dir, 'obs_project', 'testuser', 'testrepo', '12345678')
        self.project_files = [f for f in os.listdir(self.project_dir) if os.path.isfile(os.path.join(self.project_dir, f))]
        self.project_key = 'u/testuser/testrepo/12345678'
        self.deployer.cdn_handler.create_bucket()
        self.deployer.door43_handler.create_bucket()
        for filename in self.project_files:
            self.deployer.cdn_handler.upload_file(os.path.join(self.project_dir, filename), '{0}/{1}'.format(self.project_key, filename))
        self.deployer.door43_handler.upload_file(os.path.join(self.resources_dir, 'templates', 'bible.html'),
                                            'templates/bible.html')
        self.deployer.door43_handler.upload_file(os.path.join(self.resources_dir, 'templates', 'obs.html'),
                                            'templates/obs.html')
