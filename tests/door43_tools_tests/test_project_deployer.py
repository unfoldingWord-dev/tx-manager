from __future__ import absolute_import, unicode_literals, print_function
import codecs
import unittest
import os
import tempfile
from bs4 import BeautifulSoup
from moto import mock_s3
from libraries.door43_tools.project_deployer import ProjectDeployer
from libraries.door43_tools.td_language import TdLanguage
from libraries.general_tools import file_utils
from libraries.general_tools.file_utils import unzip
from libraries.app.app import App
from shutil import rmtree


@mock_s3
class ProjectDeployerTests(unittest.TestCase):
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName))
        App.cdn_s3_handler().create_bucket()
        App.door43_s3_handler().create_bucket()
        self.temp_dir = tempfile.mkdtemp(prefix="test_project_deployer")
        self.deployer = ProjectDeployer()
        TdLanguage.language_list = {
            'aa': TdLanguage({'gw': False, 'ld': 'ltr', 'ang': 'Afar', 'lc': 'aa', 'ln': 'Afaraf', 'lr': 'Africa',
                              'pk': 6}),
            'en': TdLanguage({'gw': True, 'ld': 'ltr', 'ang': 'English', 'lc': 'en', 'ln': 'English',
                              'lr': 'Europe', 'pk': 1747}),
            'es': TdLanguage({'gw': True, 'ld': 'ltr', 'ang': 'Spanish', 'lc': 'es', 'ln': 'espa\xf1ol',
                              'lr': 'Europe', 'pk': 1776}),
            'fr': TdLanguage({'gw': True, 'ld': 'ltr', 'ang': 'French', 'lc': 'fr',
                              'ln': 'fran\xe7ais, langue fran\xe7aise', 'lr': 'Europe', 'pk': 1868})
        }

    def tearDown(self):
        rmtree(self.temp_dir, ignore_errors=True)

    def test_obs_deploy_revision_to_door43(self):
        self.mock_s3_obs_project()
        build_log_key = '{0}/build_log.json'.format(self.project_key)
        ret = self.deployer.deploy_revision_to_door43(build_log_key)
        self.assertTrue(ret)
        self.assertTrue(App.door43_s3_handler().key_exists(build_log_key))
        self.assertTrue(App.door43_s3_handler().key_exists('{0}/50.html'.format(self.project_key)))

    def test_obs_deploy_revision_to_door43_exception(self):
        self.mock_s3_obs_project()
        build_log_key = '{0}/build_log.json'.format(self.project_key)
        self.deployer.run_templater = self.mock_run_templater_exception
        ret = self.deployer.deploy_revision_to_door43(build_log_key)
        self.assertFalse(ret)

    def test_bad_deploy_revision_to_door43(self):
        self.mock_s3_obs_project()
        bad_key = 'u/test_user/test_repo/12345678/bad_build_log.json'
        ret = self.deployer.deploy_revision_to_door43(bad_key)
        self.assertFalse(ret)

    def test_bible_deploy_part_revision_to_door43(self):
        # given
        test_repo_name = 'en-ulb-4-books-multipart.zip'
        project_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.mock_s3_bible_project(test_repo_name, project_key)
        part = 1
        build_log_key = '{0}/{1}/build_log.json'.format(self.project_key, part)
        output_file = '02-EXO.html'
        output_key = '{0}/{1}'.format(self.project_key, output_file)
        expect_success = True

        # when
        ret = self.deployer.deploy_revision_to_door43(build_log_key)

        # then
        self.validate_bible_results(ret, build_log_key, expect_success, output_key)

    def test_bible_deploy_part_revision_to_door43_exception(self):
        # given
        test_repo_name = 'en-ulb-4-books-multipart.zip'
        project_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.mock_s3_bible_project(test_repo_name, project_key)
        part = 1
        build_log_key = '{0}/{1}/build_log.json'.format(self.project_key, part)
        self.deployer.run_templater = self.mock_run_templater_exception

        # when
        ret = self.deployer.deploy_revision_to_door43(build_log_key)

        # then
        self.assertFalse(ret)

    def test_bible_deploy_part_not_ready_revision_to_door43(self):
        # given
        test_repo_name = 'en-ulb-4-books-multipart.zip'
        project_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.mock_s3_bible_project(test_repo_name, project_key)
        part = 0
        build_log_key = '{0}/{1}/build_log.json'.format(self.project_key, part)
        expect_success = False

        # when
        ret = self.deployer.deploy_revision_to_door43(build_log_key)

        # then
        self.validate_bible_results(ret, build_log_key, expect_success, None)

    def test_bible_deploy_part_file_missing_revision_to_door43(self):
        # given
        test_repo_name = 'en-ulb-4-books-multipart.zip'
        project_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.mock_s3_bible_project(test_repo_name, project_key)
        part = 2
        build_log_key = '{0}/{1}/build_log.json'.format(self.project_key, part)
        expect_success = True

        # when
        ret = self.deployer.deploy_revision_to_door43(build_log_key)

        # then
        self.validate_bible_results(ret, build_log_key, expect_success, None)

    def test_bible_deploy_mutli_part_merg_revision_to_door43(self):
        # given
        test_repo_name = 'en-ulb-4-books-multipart.zip'
        project_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.mock_s3_bible_project(test_repo_name, project_key, True)
        self.set_deployed_flags(project_key, 4)
        build_log_key = '{0}/build_log.json'.format(self.project_key)
        expect_success = True
        output_file = '02-EXO.html'
        output_key = '{0}/{1}'.format(self.project_key, output_file)

        # when
        ret = self.deployer.deploy_revision_to_door43(build_log_key)

        # then
        self.validate_bible_results(ret, build_log_key, expect_success, output_key)

    def test_bible_deploy_mutli_part_merg_revision_to_door43_exception(self):
        # given
        test_repo_name = 'en-ulb-4-books-multipart.zip'
        project_key = 'u/tx-manager-test-data/en-ulb/22f3d09f7a'
        self.mock_s3_bible_project(test_repo_name, project_key, True)
        build_log_key = '{0}/build_log.json'.format(self.project_key)
        self.deployer.run_templater = self.mock_run_templater_exception

        # when
        ret = self.deployer.deploy_revision_to_door43(build_log_key)

        # then
        self.assertFalse(ret)

    def test_redeploy_all_projects(self):
        self.mock_s3_obs_project()
        App.cdn_s3_handler().put_contents('u/user1/project1/revision1/build_log.json', '{}')
        App.cdn_s3_handler().put_contents('u/user2/project2/revision2/build_log.json', '{}')
        self.assertTrue(self.deployer.redeploy_all_projects('test-door43_deployer'))

    #
    # helpers
    #

    def validate_bible_results(self, ret, build_log_key, expect_success, output_key):
        self.assertEqual(ret, expect_success)
        if expect_success:
            if output_key:
                self.assertTrue(App.door43_s3_handler().key_exists(output_key))

    def mock_run_templater_exception(self):
        raise NotImplementedError("Test Exception")

    def mock_s3_obs_project(self):
        zip_file = os.path.join(self.resources_dir, 'converted_projects', 'en-obs-complete.zip')
        out_dir = os.path.join(self.temp_dir, 'en-obs-complete')
        unzip(zip_file, out_dir)
        project_dir = os.path.join(out_dir, 'door43', 'en-obs', '12345678')
        self.project_files = [f for f in os.listdir(project_dir) if os.path.isfile(os.path.join(project_dir, f))]
        self.project_key = 'u/door43/en-obs/12345678'
        for filename in self.project_files:
            App.cdn_s3_handler().upload_file(os.path.join(project_dir, filename), '{0}/{1}'.format(self.project_key,
                                                                                                 filename))
        App.cdn_s3_handler().upload_file(os.path.join(out_dir, 'door43', 'en-obs', 'project.json'),
                                       'u/door43/en-obs/project.json')
        App.door43_s3_handler().upload_file(os.path.join(self.resources_dir, 'templates', 'project-page.html'),
                                          'templates/project-page.html')

    def set_deployed_flags(self, project_key, part_count, skip=-1):
        tempf = tempfile.mktemp(prefix="temp", suffix="deployed")
        file_utils.write_file(tempf, ' ')
        for i in range(0, part_count):
            if i != skip:
                key = '{0}/{1}/deployed'.format(project_key, i)
                App.cdn_s3_handler().upload_file(tempf, key, cache_time=0)
        os.remove(tempf)

    def mock_s3_bible_project(self, test_file_name, project_key, multi_part=False):
        converted_proj_dir = os.path.join(self.resources_dir, 'converted_projects')
        test_file_base = test_file_name.split('.zip')[0]
        zip_file = os.path.join(converted_proj_dir, test_file_name)
        out_dir = os.path.join(self.temp_dir, test_file_base)
        unzip(zip_file, out_dir)
        project_dir = os.path.join(out_dir, test_file_base) + os.path.sep
        self.project_files = file_utils.get_files(out_dir)
        self.project_key = project_key
        for filename in self.project_files:
            sub_path = filename.split(project_dir)[1].replace(os.path.sep, '/')  # Make sure it is a bucket path
            App.cdn_s3_handler().upload_file(filename, '{0}/{1}'.format(project_key, sub_path))

            if multi_part:  # copy files from cdn to door43
                base_name = os.path.basename(filename)
                if '.html' in base_name:
                    with codecs.open(filename, 'r', 'utf-8-sig') as f:
                        soup = BeautifulSoup(f, 'html.parser')

                    # add nav tag
                    new_tag = soup.new_tag('div', id='right-sidebar')
                    soup.body.append(new_tag)
                    html = unicode(soup)
                    file_utils.write_file(filename, html.encode('ascii', 'xmlcharrefreplace'))

                App.door43_s3_handler().upload_file(filename, '{0}/{1}'.format(project_key, base_name))

        # u, user, repo = project_key
        App.door43_s3_handler().upload_file(os.path.join(self.resources_dir, 'templates', 'project-page.html'),
                                          'templates/project-page.html')
