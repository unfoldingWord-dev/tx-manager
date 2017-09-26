from __future__ import print_function, absolute_import, unicode_literals
import json
import tempfile
import unittest
import os
import codecs
import sys
import requests
import shutil
import time
from unittest import TestCase
from bs4 import BeautifulSoup
from libraries.general_tools import file_utils
from libraries.manager.manager import TxManager
from libraries.general_tools.file_utils import unzip
from libraries.client.client_webhook import ClientWebhook
from libraries.models.manifest import TxManifest
from libraries.models.job import TxJob
from libraries.app.app import App

# replace default print with utf-8 writer, so it can work with pipes and redirects such as used with the latest
#   Travis build system.
UTF8Writer = codecs.getwriter('utf8')
sys.stdout = UTF8Writer(sys.stdout)

# defines
COMMIT_LENGTH = 40
USE_WEB_HOOK_LAMBDA = True
BIBLE_LIST_NT = ["41-MAT", "42-MRK", "43-LUK", "44-JHN", "45-ACT", "46-ROM", "47-1CO", "48-2CO", "49-GAL", "50-EPH",
      "51-PHP", "52-COL", "53-1TH", "54-2TH", "55-1TI", "56-2TI", "57-TIT", "58-PHM", "59-HEB", "60-JAS",
      "61-1PE", "62-2PE", "63-1JN", "64-2JN", "65-3JN", "66-JUD", "67-REV"]
BIBLE_LIST_OT = ["01-GEN", "02-EXO", "03-LEV", "04-NUM", "05-DEU", "06-JOS", "07-JDG", "08-RUT", "09-1SA", "10-2SA",
      "11-1KI", "12-2KI", "13-1CH", "14-2CH", "15-EZR", "16-NEH", "17-EST", "18-JOB", "19-PSA", "20-PRO",
      "21-ECC", "22-SNG", "23-ISA", "24-JER", "25-LAM", "26-EZK", "27-DAN", "28-HOS", "29-JOL", "30-AMO",
      "31-OBA", "32-JON", "33-MIC", "34-NAM", "35-HAB", "36-ZEP", "37-HAG", "38-ZEC", "39-MAL", ]
FULL_BIBLE_LIST = BIBLE_LIST_OT + BIBLE_LIST_NT


class TestConversions(TestCase):
    """
    To test locally, you must set two environment variables:

        set TEST_DEPLOYED to "test_deployed"
        set GOGS_USER_TOKEN to tx-manager user token
        set DB_PASS to the password of this environment's RDS DB (e.g. dev-tx)

    Integration test will run on dev unless TRAVIS_BRANCH is set to 'master' (then will run on prod),
    or set to 'test' and will run on the test environment
    """

    @classmethod
    def setUpClass(cls):
        """Runs before all tests."""
        branch = os.environ.get('TRAVIS_BRANCH', 'develop')  # default is testing develop branch (dev)
        gogs_user_token = os.environ.get('GOGS_USER_TOKEN', '')
        db_pass = os.environ.get('DB_PASS', '')

        if not db_pass:
            db_pass = os.eniron.get('{0}_DB_PASS'.format(branch.upper()), '')

        if branch == 'master':
            prefix = ''  # no prefix for production
        elif branch == 'test':
            prefix = 'test-'  # For running on test
        else:
            prefix = 'dev-'  # default

        App(prefix=prefix, gogs_user_token=gogs_user_token, db_pass=db_pass)

        App.logger.debug('Testing on \'' + branch + '\' branch, e.g.: ' + App.api_url)

    def setUp(self):
        """Runs before each test."""
        self.warnings = []

    def tearDown(self):
        """Runs after each test."""
        # delete temp files
        if hasattr(self, 'temp_dir') and os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_usfm_en_udb_bundle_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/en_udb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_names = FULL_BIBLE_LIST

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_names, job)

    def test_ts_mat_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/kpb_mat_text_udb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "41-MAT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    def test_ts_acts0_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/awa_act_text_reg.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    def test_ts_psa_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/ceb_psa_text_ulb_L3.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "19-PSA"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    def test_obs_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/en-obs-rc-0.2.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_chapter_count = 50

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path, "", job,
                                 chapter_count=expected_chapter_count, file_ext="md")

    def test_obs_conversion_ts_upload(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/hu_obs_text_obs.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_chapter_count = 49

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path, "", job,
                                 chapter_count=expected_chapter_count, file_ext="md")

    def test_usfm_en_jud_bundle_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/en-ulb-jud.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_names = [ "66-JUD" ]

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_names, job)

    def test_usfm_en_bundle_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/en-ulb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_names = ["01-GEN", "02-EXO", "03-LEV", "04-NUM", "05-DEU", "06-JOS"]

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_names, job)

    # @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_usfm_ru_short_bundle_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        # shorter book list, but bigger books
        git_url = "https://git.door43.org/tx-manager-test-data/bible_ru_short.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_names = ["18-JOB", "19-PSA", "20-PRO", "21-ECC", "22-SNG", "23-ISA", "24-JER", ]

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_names, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_usfm_ru_nt_bundle_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/nt_ru.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_names = BIBLE_LIST_NT

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_names, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_usfm_ru_ot_bundle_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/ot_ru.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_names = BIBLE_LIST_OT

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_names, job)

    @unittest.skip("#### TODO: Skipping broken conversion that needs to be fixed - webhook takes too long and times out")
    def test_usfm_ru_bundle_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/bible_ru.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_names = FULL_BIBLE_LIST

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_names, job)

    def test_ts_acts1_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/kan-x-aruvu_act_text_udb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    def test_ts_acts2_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/mohanraj/kn-x-bedar_act_text_udb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts3_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/nirmala/te-x-budugaja_act_text_reg.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts4_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/jathapu/kxv_act_text_udb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts5_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/vinaykumar/kan-x-thigularu_act_text_udb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts6_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/Zipson/yeu_act_text_udb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts7_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/Zipson/kfc_act_text_udb.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts8_conversion(self):
        # given
        if not self.is_testing_enabled():
            return  # skip test if integration test not enabled
        git_url = "https://git.door43.org/E01877C8393A/uw-act_udb-aen.git"
        base_url, repo, user = self.get_parts_of_git_url(git_url)
        expected_output_name = "45-ACT"

        # when
        build_log_json, commit_id, commit_path, commit_sha, success, job = self.do_conversion_for_repo(base_url, user,
                                                                                                       repo)

        # then
        self.validate_conversion(user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                                 expected_output_name, job)

    #
    # handlers
    #

    def is_testing_enabled(self):
        test = os.environ.get('TEST_DEPLOYED', "")
        do_test = (test == "test_deployed")
        if not do_test:
            App.logger.debug("Skip testing since TEST_DEPLOYED is not set")
        else:
            gogs_user_token = os.environ.get('GOGS_USER_TOKEN', "")
            self.assertTrue(len(gogs_user_token) > 0, "GOGS_USER_TOKEN is missing in environment")
        return do_test

    def get_parts_of_git_url(self, git_url):
        App.logger.debug("Testing conversion of: " + git_url)
        parts = git_url.split("/")
        base_url = "/".join(parts[0:3])
        user = parts[3]
        repo = parts[4].split(".git")[0]
        return base_url, repo, user

    def validate_conversion(self, user, repo, success, build_log_json, commit_id, commit_sha, commit_path,
                            expected_output_names, job, chapter_count=-1, file_ext=""):
        self.assertTrue(len(build_log_json) > 0)
        self.assertIsNotNone(job)
        self.temp_dir = tempfile.mkdtemp(prefix='testing_')

        if not (type(expected_output_names) is list):
            expected_output_names = [expected_output_names]  # put string in list

        # check pre-convert files
        self.download_and_check_zip_file(self.preconvert_handler, expected_output_names, "usfm",
                                         self.get_preconvert_s3_key(commit_sha), "preconvert", success, chapter_count,
                                         file_ext)

        # check converted files
        destination_key = self.get_destination_s3_key(commit_sha, repo, user)
        converted_build_log = self.check_destination_files(self.cdn_handler, expected_output_names, "html",
                                                           destination_key, chapter_count)

        # check required fields
        App.logger.debug(converted_build_log)
        saved_build_json = json.loads(converted_build_log)
        self.assertTrue('commit_id' in saved_build_json)
        self.assertTrue('repo_owner' in saved_build_json)
        self.assertTrue('repo_name' in saved_build_json)
        self.assertTrue('created_at' in saved_build_json)
        self.assertTrue('source' in saved_build_json)
        self.assertTrue('errors' in saved_build_json)
        self.assertTrue('warnings' in saved_build_json)
        self.assertTrue('message' in saved_build_json)
        self.assertTrue('status' in saved_build_json)

        self.assertEqual(len(commit_id), COMMIT_LENGTH)
        self.assertIsNotNone(commit_sha)
        self.assertIsNotNone(commit_path)
        if len(job.errors) > 0:
            self.warn("WARNING: Found job errors: " + str(job.errors))

        if len(build_log_json['errors']) > 0:
            self.warn("WARNING: Found build_log errors: " + str(build_log_json['errors']))

        door43_handler = App.door43_s3_handler()
        deployed_build_log = self.check_deployed_files(door43_handler, expected_output_names, "html",
                                                       destination_key, chapter_count)

        self.compare_build_logs(converted_build_log, deployed_build_log, destination_key)

        if len(self.warnings):
            App.logger.debug("\n#######\nHave warnings:\n#######\n" + '\n'.join(self.warnings))

        self.assertTrue(success)

        # Test that repo is in manifest table
        tx_manifest = TxManifest.get(repo_name=repo, user_name=user)
        # Giving TxManifest above just the composite keys will cause it to load all the data from the App.
        self.assertIsNotNone(tx_manifest)
        self.assertEqual(tx_manifest.repo_name, repo)
        self.assertEqual(tx_manifest.user_name, user)

    def compare_build_logs(self, converted_build_log, deployed_build_log, destination_key):
        keys = ["callback", "cdn_bucket", "cdn_file", "commit_id", "commit_message", "commit_url", "committed_by",
                "compare_url", "convert_module", "created_at", "errors", "identifier", "input_format", "job_id", "log",
                "output", "output_format", "repo_name", "repo_owner", "resource_type", "source", "status", "success",
                "user", "warnings"]

        if converted_build_log != deployed_build_log:
            converted_build_log = App.cdn_s3_handler().get_file_contents(
                os.path.join(destination_key, "build_log.json"))  # make sure we have the latest
        if converted_build_log != deployed_build_log:
            deployed_build_log_ = json.loads(deployed_build_log)
            converted_build_log_ = json.loads(converted_build_log)
            for key in keys:
                if key not in converted_build_log_:
                    self.warn("Key {0} missing in converted_build_log".format(key))
                    continue
                if key not in deployed_build_log_:
                    self.warn("Key {0} missing in deployed_build_log".format(key))
                    continue
                converted_value = converted_build_log_[key]
                deployed_value = deployed_build_log_[key]
                if converted_value != deployed_value:
                    self.warn("miscompare build of logs in key {0}: '{1}' - '{2}'".format(key, converted_value,
                                                                                          deployed_value))

    def download_and_check_zip_file(self, handler, expected_output_files, extension, key, file_type, success,
                                    chapter_count=-1, file_ext=""):
        zip_path = os.path.join(self.temp_dir, file_type + ".zip")
        handler.download_file(key, zip_path)
        temp_sub_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix=file_type + "_")
        unzip(zip_path, temp_sub_dir)

        check_list = []
        if chapter_count <= 0:
            for file_name in expected_output_files:
                check_list.append(file_name + "." + extension)
        else:
            check_list = ['{0:0>2}.{1}'.format(i, file_ext) for i in range(1, chapter_count + 1)]

        is_first = True
        for file_name in check_list:
            output_file_path = os.path.join(temp_sub_dir, file_name)
            App.logger.debug("checking preconvert zip for: " + output_file_path)
            self.assertTrue(os.path.exists(output_file_path), "missing file: " + file_name)
            if is_first:
                self.print_file(file_name, output_file_path)
                is_first = False

        manifest_json = os.path.join(temp_sub_dir, "manifest.json")
        json_exists = os.path.exists(manifest_json)
        if not success and json_exists:  # print out for troubleshooting
            self.print_file("manifest.json", manifest_json)
        manifest_yaml = os.path.join(temp_sub_dir, "manifest.yaml")
        yaml_exists = os.path.exists(manifest_yaml)
        if not success and yaml_exists:  # print out for troubleshooting
            self.print_file("manifest.yaml", manifest_yaml)

        self.assertTrue(json_exists or yaml_exists, "missing manifest file")

    def warn(self, message):
        self.warnings.append(message)
        App.logger.debug(message)

    def print_file(self, file_name, file_path):
        text = file_utils.read_file(file_path)[:200]  # get the start of the file
        App.logger.debug("\nOutput file (" + file_name + "): " + text + "\n")

    def check_deployed_files(self, handler, expected_output_files, extension, key, chapter_count=-1):
        check_list = []
        if chapter_count <= 0:
            for file_name in expected_output_files:
                check_list.append(file_name + "." + extension)
        else:
            check_list = ['{0:0>2}.html'.format(i) for i in range(1, chapter_count + 1)]
            # checkList.append("index.html")

        check_list.append("index.html")

        start_time = time.time()
        time_out = 60
        found = []
        while len(found) < len(check_list):
            elapsed_seconds = elapsed_time(start_time)
            if elapsed_seconds > time_out:
                self.warn("timeout ({0} sec) getting deployed files".format(elapsed_seconds))
                break

            time.sleep(5)
            for file_name in check_list:
                if file_name in found:
                    continue

                path = os.path.join(key, file_name)
                App.logger.debug("checking destination folder for: " + path)
                output = handler.get_file_contents(path)
                if output:
                    found.append(file_name)
                    retries = 0  # reset
                    App.logger.debug("found: " + path)

        if len(found) < len(check_list):
            for file_name in check_list:
                if file_name not in found:
                    self.assertTrue(False, "missing file: " + file_name)

        build_log = handler.get_file_contents(os.path.join(key, "build_log.json"))
        manifest = handler.get_file_contents(os.path.join(key, "manifest.json"))
        if manifest is None:
            manifest = handler.get_file_contents(os.path.join(key, "manifest.yaml"))
        self.assertTrue(len(manifest) > 0, "missing manifest file ")
        self.assertTrue(len(build_log) > 0, "missing build_log file ")
        return build_log

    def check_destination_files(self, handler, expected_output_files, extension, key, chapter_count=-1):
        check_list = []
        if chapter_count <= 0:
            for file_name in expected_output_files:
                check_list.append(file_name + "." + extension)
        else:
            check_list = ['{0:0>2}.html'.format(i) for i in range(1, chapter_count + 1)]
            # checkList.append("index.html")

        start_time = time.time()
        time_out = 60
        for file_name in check_list:
            path = os.path.join(key, file_name)
            App.logger.debug("checking destination folder for: " + path)
            output = handler.get_file_contents(path)
            while output is None:  # try again in a moment since upload files may not be finished
                elapsed_seconds = elapsed_time(start_time)
                if elapsed_seconds > time_out:
                    self.warn("timeout ({0} sec) getting file: {1}".format(elapsed_seconds, path))
                    break

                # App.logger.debug("retry fetch of: " + path)
                output = handler.get_file_contents(path)
                if output is None:
                    time.sleep(5)

            self.assertIsNotNone(output, "missing file: " + path)

        build_log = handler.get_file_contents(os.path.join(key, "build_log.json"))
        manifest = handler.get_file_contents(os.path.join(key, "manifest.json"))
        if manifest is None:
            manifest = handler.get_file_contents(os.path.join(key, "manifest.yaml"))
        self.assertTrue(len(manifest) > 0, "missing manifest file ")
        self.assertTrue(len(build_log) > 0, "missing build_log file ")
        return build_log

    def do_conversion_for_repo(self, base_url, user, repo):
        build_log_json = None
        job = None
        success = False
        self.cdn_handler = App.cdn_s3_handler()
        # TODO: change this to use gogs API when finished
        commit_id, commit_path, commit_sha = self.fetch_commit_data_for_repo(base_url, repo, user)
        commit_len = len(commit_id)
        if commit_len == COMMIT_LENGTH:
            self.delete_preconvert_zip_file(commit_sha)
            self.delete_tx_output_zip_file(commit_id)
            self.empty_destination_folder(commit_sha, repo, user)
            build_log_json, success, job = self.do_conversion_job(base_url, commit_id, commit_path, commit_sha, repo,
                                                                  user)

        return build_log_json, commit_id, commit_path, commit_sha, success, job

    def empty_destination_folder(self, commit_sha, repo, user):
        destination_key = self.get_destination_s3_key(commit_sha, repo, user)
        for obj in App.cdn_s3_handler().get_objects(prefix=destination_key):
            App.logger.debug("deleting destination file: " + obj.key)
            App.cdn_s3_handler().delete_file(obj.key)

    def delete_preconvert_zip_file(self, commit_sha):
        self.preconvert_handler = App.pre_convert_s3_handler()
        preconvert_key = self.get_preconvert_s3_key(commit_sha)
        if App.pre_convert_s3_handler().key_exists(preconvert_key):
            App.logger.debug("deleting preconvert file: " + preconvert_key)
            App.pre_convert_s3_handler().delete_file(preconvert_key, catch_exception=True)

    def delete_tx_output_zip_file(self, commit_id):
        tx_output_key = self.get_tx_output_s3_key(commit_id)
        if App.cdn_s3_handler().key_exists(tx_output_key):
            App.logger.debug("deleting tx output file: " + tx_output_key)
            App.cdn_s3_handler().delete_file(tx_output_key, catch_exception=True)

    def get_tx_output_s3_key(self, commit_id):
        output_key = 'tx/job/{0}.zip'.format(commit_id)
        return output_key

    def get_destination_s3_key(self, commit_sha, repo, user):
        destination_key = 'u/{0}/{1}/{2}'.format(user, repo, commit_sha)
        return destination_key

    def get_preconvert_s3_key(self, commit_sha):
        preconvert_key = "preconvert/{0}.zip".format(commit_sha)
        return preconvert_key

    def do_conversion_job(self, base_url, commit_id, commit_path, commit_sha, repo, user):
        commit_data = {
            "after": commit_id,
            "commits": [
                {
                    "id": "b9278437b27024e07d02490400138d4fd7d1677c",
                    "message": "Fri Dec 16 2016 11:09:07 GMT+0530 (India Standard Time)\n",
                    "url": base_url + commit_path,
                }],
            "compare_url": "",
            "repository": {
                "name": repo,
                "owner": {
                    "id": 1234567890,
                    "username": user,
                    "full_name": user,
                    "email": "you@example.com"
                },
            },
            "pusher": {
                "id": 123456789,
                "username": "test",
                "full_name": "",
                "email": "you@example.com"
            },
        }

        start = time.time()
        if USE_WEB_HOOK_LAMBDA:
            headers = {"content-type": "application/json"}
            tx_client_webhook_url = "{0}/client/webhook".format(App.api_url)
            App.logger.debug('Making request to client/webhook URL {0} with payload:'.format(tx_client_webhook_url))
            App.logger.debug(commit_data)
            response = requests.post(tx_client_webhook_url, json=commit_data, headers=headers)
            App.logger.debug('webhook finished with code:' + str(response.status_code))
            App.logger.debug('webhook finished with text:' + str(response.text))
            build_log_json = json.loads(response.text)
            if response.status_code == 504:  # on timeout, could be multi-part, so try to get build
                build_log_json = self.poll_for_build_log(commit_sha, repo, user)

            elif response.status_code != 200:
                job_id = None if 'job_id' not in build_log_json else build_log_json['job_id']
                return build_log_json, False, job_id

        else:
            # do preconvert locally
            try:
                build_log_json = ClientWebhook(commit_data=commit_data).process_webhook()
            except Exception as e:
                message = "Exception: " + str(e)
                self.warn(message)
                return None, False, None

        App.logger.debug("webhook completed in " + str(elapsed_time(start)) + " seconds")

        if "build_logs" not in build_log_json:  # if not multiple parts
            job_id = build_log_json['job_id']
            if job_id is None:
                self.warn("Job ID missing in build_log")
                return None, False, None
            success, job = self.poll_until_job_finished(job_id)

        else:  # multiple parts
            success, job = self.poll_until_all_jobs_finished(build_log_json['build_logs'])

        build_log_json = self.get_json_file(commit_sha, 'build_log.json', repo, user)
        if build_log_json is not None:
            App.logger.debug("Final results:\n" + str(build_log_json))
        return build_log_json, success, job

    def poll_for_build_log(self, commit_sha, repo, user):
        build_log_json = {}
        for i in range(0, 60):
            time.sleep(5)
            build_log_json = self.get_json_file(commit_sha, 'build_log.json', repo, user)
            if build_log_json:
                break
        return build_log_json

    def poll_until_all_jobs_finished(self, build_logs):
        job = None
        finished = []
        job_count = len(build_logs)
        polling_timeout = 5 * 60  # poll for up to 5 minutes for job to complete or error
        sleep_interval = 5  # how often to check for completion
        done = False
        start = time.time()
        end = start + polling_timeout
        while (time.time() < end) and not done:
            time.sleep(sleep_interval)  # delay before polling again
            for build_log in build_logs:  # check for completion of each part
                job_id = build_log['job_id']
                if job_id in finished:
                    continue  # skip if job already finished

                job = TxJob.get(job_id)
                self.assertIsNotNone(job)
                App.logger.debug("job " + job_id + " status at " + str(elapsed_time(start)) + ":\n" + str(job.log))

                if job.ended_at is not None:
                    finished.append(job_id)
                    end = time.time() + polling_timeout  # reset timeout
                    if len(finished) >= job_count:
                        done = True  # finished
                        break

        if len(finished) < job_count:
            for build_log in build_logs:  # check for completion of each part
                job_id = build_log['job_id']
                if job_id not in finished:
                    self.warn("Timeout watiting for start on job: " + job_id)

        return done, job

    def poll_until_job_finished(self, job_id):
        success = False
        job = None
        polling_timeout = 5 * 60  # poll for up to 5 minutes for job to complete or error
        sleep_interval = 5  # how often to check for completion
        start = time.time()
        end = start + polling_timeout
        while time.time() < end:
            time.sleep(sleep_interval)
            job = TxJob.get(job_id)
            self.assertIsNotNone(job)
            elapsed_seconds = elapsed_time(start)
            App.logger.debug("job " + job_id + " status at " + str(elapsed_seconds) + ":\n" + str(job.log))

            if job.ended_at is not None:
                success = True
                break

        if not success:
            self.warn("Timeout Waiting for start on job: " + job_id)

        return success, job

    def get_json_file(self, commit_sha, file_name, repo, user):
        key = 'u/{0}/{1}/{2}/{3}'.format(user, repo, commit_sha, file_name)
        text = App.cdn_s3_handler().get_json(key)
        return text

    def fetch_commit_data_for_repo(self, base_url, repo, user):
        commit_id = None
        commit_sha = None
        commit_path = None
        data = self.read_contents_of_repo(base_url, user, repo)
        if len(data) > 10:
            commit_id, commit_sha, commit_path = self.find_lasted_commit_from_page(data)
        return commit_id, commit_path, commit_sha

    def find_lasted_commit_from_page(self, text):
        soup = BeautifulSoup(text, 'html.parser')
        table = soup.find('table')
        commit_id = None
        commit_sha = None
        commit_path = None
        if table is not None:
            rows = table.findAll('tr')
            if (rows is not None) and (len(rows) > 0):
                for row in rows:
                    commit_cell = row.find('td', {"class": "sha"})
                    if commit_cell is not None:
                        commit_link = commit_cell.find('a')
                        if commit_link is not None:
                            commit_path = commit_link['href']
                            commit_sha = self.get_contents(commit_link)
                            parts = commit_path.split('/')
                            commit_id = parts[4]
                            break

        return commit_id, commit_sha, commit_path

    def make_folder(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def read_contents_of_repo(self, base_url, user, repo):
        self.url = "{0}/{1}/{2}/commits/master".format(base_url, user, repo)
        ttr_response = requests.get(self.url)
        if ttr_response.status_code == 200:
            return ttr_response.text

        App.logger.debug("Failed to load: " + self.url)
        return None

    def get_contents(self, item):
        if item is not None:
            contents = item.stripped_strings
            for string in contents:
                text = string
                return text
        return None


def elapsed_time(start_time):
    elapsed_seconds = int(time.time() - start_time)
    return elapsed_seconds
