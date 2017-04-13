from __future__ import absolute_import, unicode_literals, print_function
import unittest
import os
import tempfile
import mock
from moto import mock_s3
from door43_tools.project_deployer import ProjectDeployer
from general_tools.file_utils import unzip
from shutil import rmtree


@mock_s3
class ProjectDeployerTests(unittest.TestCase):
    MOCK_CDN_BUCKET = "test_cdn"
    MOCK_DOOR43_BUCKET = "test_door43"

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_project_deployer")
        self.deployer = ProjectDeployer(self.MOCK_CDN_BUCKET, self.MOCK_DOOR43_BUCKET)
        self.deployer.cdn_handler.create_bucket()
        self.deployer.door43_handler.create_bucket()
        self.mock_s3_obs_project()

    def tearDown(self):
        rmtree(self.temp_dir, ignore_errors=True)

    def test_obs_deploy_revision_to_door43(self):
        build_log_key = '{0}/build_log.json'.format(self.project_key)
        ret = self.deployer.deploy_revision_to_door43(build_log_key)
        self.assertTrue(ret)
        self.assertTrue(self.deployer.door43_handler.key_exists(build_log_key))
        self.assertTrue(self.deployer.door43_handler.key_exists('{0}/50.html'.format(self.project_key)))

    def test_bad_deploy_revision_to_door43(self):
        bad_key = 'u/test_user/test_repo/12345678/bad_build_log.json'
        ret = self.deployer.deploy_revision_to_door43(bad_key)
        self.assertFalse(ret)

    def test_redeploy_all_projects(self):
        self.deployer.cdn_handler.put_contents('u/user1/project1/revision1/build_log.json', '{}')
        self.deployer.cdn_handler.put_contents('u/user2/project2/revision2/build_log.json', '{}')
        self.assertTrue(self.deployer.redeploy_all_projects())

    def mock_s3_obs_project(self):
        zip_file = os.path.join(self.resources_dir, 'converted_projects', 'en-obs-complete.zip')
        out_dir = os.path.join(self.temp_dir, 'en-obs-complete')
        unzip(zip_file, out_dir)
        project_dir = os.path.join(out_dir, 'door43', 'en-obs', '12345678')
        self.project_files = [f for f in os.listdir(project_dir) if os.path.isfile(os.path.join(project_dir, f))]
        self.project_key = 'u/door43/en-obs/12345678'
        for filename in self.project_files:
            self.deployer.cdn_handler.upload_file(os.path.join(project_dir, filename), '{0}/{1}'.format(self.project_key, filename))
        self.deployer.cdn_handler.upload_file(os.path.join(out_dir, 'door43', 'en-obs', 'project.json'), 'u/door43/en-obs/project.json')
        self.deployer.door43_handler.upload_file(os.path.join(self.resources_dir, 'templates', 'bible.html'),
                                            'templates/bible.html')
        self.deployer.door43_handler.upload_file(os.path.join(self.resources_dir, 'templates', 'obs.html'),
                                            'templates/obs.html')
