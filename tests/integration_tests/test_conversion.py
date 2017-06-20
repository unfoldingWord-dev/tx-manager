# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import json
import tempfile
import unittest
import os
from unittest import TestCase
import requests
import shutil
import time
from libraries.general_tools import file_utils
from libraries.manager.manager import TxManager
from libraries.general_tools.file_utils import unzip
from libraries.aws_tools.s3_handler import S3Handler
from libraries.client.client_webhook import ClientWebhook
from bs4 import BeautifulSoup

COMMIT_LENGTH = 40
USE_WEB_HOOK_LAMBDA = True

class TestConversions(TestCase):
    """
    To test locally, you must set two environment variables:

        set TEST_DEPLOYED to "test_deployed"
        set GOGS_USER_TOKEN to tx-manager user token

    Integration test will run on dev unless TRAVIS_BRANCH is set to 'master' (then will run on prod)
    """

    def setUp(self):
        branch = os.environ.get("TRAVIS_BRANCH", "develop") # default is testing develop branch (dev)

        destination = "dev-" # default
        if branch == "master":
            destination = "" # no prefix for production

        self.destination = destination
        self.api_url = 'https://{0}api.door43.org'.format(destination)
        self.pre_convert_bucket = '{0}tx-webhook-client'.format(destination)
        self.gogs_url = 'https://git.door43.org'.format(destination)
        self.cdn_bucket = '{0}cdn.door43.org'.format(destination)
        self.job_table_name = '{0}tx-job'.format(destination)
        self.module_table_name = '{0}tx-module'.format(destination)
        self.cdn_url = 'https://{0}cdn.door43.org'.format(destination)

        print("Testing on '" + branch + "' branch, e.g.: " + self.api_url)

    def tearDown(self):
        """Runs after each test."""
        # delete temp files
        if hasattr(self, 'temp_dir') and os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ts_mat_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/kpb_mat_text_udb.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "41-MAT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    def test_ts_acts0_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/awa_act_text_reg.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    def test_ts_psa_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/ceb_psa_text_ulb_L3.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "19-PSA"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    def test_obs_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/en-obs-rc-0.2.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedChapterCount = 50

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, "", job, chapterCount=expectedChapterCount, fileExt="md")

    def test_obs_conversion_ts_upload(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/hu_obs_text_obs.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedChapterCount = 49

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, "", job, chapterCount=expectedChapterCount, fileExt="md")

    def test_usfm_en_jud_bundle_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/en-ulb-jud.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputNames = [ "66-JUD" ]

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputNames, job)

    @unittest.skip("Skipping broken conversion that needs to be fixed - conversion takes too long and times out")
    def test_usfm_en_bundle_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/en-ulb.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputNames = [ "01-GEN", "02-EXO", "03-LEV", "05-DEU" ]

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputNames, job)

    @unittest.skip("Skipping broken conversion that needs to be fixed - conversion takes too long and times out")
    def test_usfm_ru_bundle_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/bible_ru.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputNames = [
            "01-GEN",
            "02-EXO",
            "03-LEV",
            "04-NUM",
            "05-DEU",
            "06-JOS",
            "07-JDG",
            "08-RUT",
            "09-1SA",
            "10-2SA",
            "11-1KI",
            "12-2KI",
            "13-1CH",
            "14-2CH",
            "15-EZR",
            "16-NEH",
            "17-EST",
            "18-JOB",
            "19-PSA",
            "20-PRO",
            "21-ECC",
            "22-SNG",
            "23-ISA",
            "24-JER",
            "25-LAM",
            "26-EZK",
            "27-DAN",
            "28-HOS",
            "29-JOL",
            "30-AMO",
            "31-OBA",
            "32-JON",
            "33-MIC",
            "34-NAM",
            "35-HAB",
            "36-ZEP",
            "37-HAG",
            "38-ZEC",
            "39-MAL",
            "41-MAT",
            "42-MRK",
            "43-LUK",
            "44-JHN",
            "45-ACT",
            "46-ROM",
            "47-1CO",
            "48-2CO",
            "49-GAL",
            "50-EPH",
            "51-PHP",
            "52-COL",
            "53-1TH",
            "54-2TH",
            "55-1TI",
            "56-2TI",
            "57-TIT",
            "58-PHM",
            "59-HEB",
            "60-JAS",
            "61-1PE",
            "62-2PE",
            "63-1JN",
            "64-2JN",
            "65-3JN",
            "66-JUD",
            "67-REV"
        ]

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputNames, job)

    def test_ts_acts1_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/tx-manager-test-data/kan-x-aruvu_act_text_udb.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    def test_ts_acts2_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/mohanraj/kn-x-bedar_act_text_udb.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts3_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/nirmala/te-x-budugaja_act_text_reg.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts4_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/jathapu/kxv_act_text_udb.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts5_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/vinaykumar/kan-x-thigularu_act_text_udb.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts6_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/Zipson/yeu_act_text_udb.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts7_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/Zipson/kfc_act_text_udb.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_ts_acts8_conversion(self):
        # given
        if not self.isTestingEnabled(): return # skip test if integration test not enabled
        git_url = "https://git.door43.org/E01877C8393A/uw-act_udb-aen.git"
        baseUrl, repo, user = self.getPartsOfGitUrl(git_url)
        expectedOutputName = "45-ACT"

        # when
        build_log_json, commitID, commitPath, commitSha, success, job = self.doConversionForRepo(baseUrl, user, repo)

        # then
        self.validateConversion(user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputName, job)

    ##
    ## handlers
    ##

    def isTestingEnabled(self):
        test = os.environ.get('TEST_DEPLOYED',"")
        doTest = (test == "test_deployed")
        if not doTest:
            print("Skip testing since TEST_DEPLOYED is not set")
        else:
            gogsUserToken = os.environ.get('GOGS_USER_TOKEN',"")
            self.assertTrue(len(gogsUserToken) > 0, "GOGS_USER_TOKEN is missing in environment")
        return doTest

    def getPartsOfGitUrl(self, git_url):
        print("Testing conversion of: " + git_url)
        parts = git_url.split("/")
        baseUrl = "/".join(parts[0:3])
        user = parts[3]
        repo = parts[4].split(".git")[0]
        return baseUrl, repo, user

    def validateConversion(self, user, repo, success, build_log_json, commitID, commitSha, commitPath, expectedOutputNames, job, chapterCount=-1, fileExt=""):
        self.assertTrue(len(build_log_json) > 0)
        self.assertIsNotNone(job)
        self.temp_dir = tempfile.mkdtemp(prefix='testing_')

        if not (type(expectedOutputNames) is list):
            expectedOutputNames = [ expectedOutputNames ] # put string in list

        # check pre-convert files
        self.downloadAndCheckZipFile(self.s3_handler, expectedOutputNames, "usfm", self.getPreconvertS3Key(commitSha),
                                     "preconvert", success, chapterCount, fileExt)

        # check deployed files
        self.checkDestinationFiles(self.cdn_handler, expectedOutputNames, "html",
                                   self.getDestinationS3Key(commitSha, repo, user), chapterCount)

        self.assertEqual(len(commitID), COMMIT_LENGTH)
        self.assertIsNotNone(commitSha)
        self.assertIsNotNone(commitPath)
        if len(job.errors) > 0:
            print("WARNING: Found job errors: " + str(job.errors))

        if len(build_log_json['errors']) > 0:
            print("WARNING: Found build_log errors: " + str(build_log_json['errors']))

        self.assertTrue(success)

    def downloadAndCheckZipFile(self, handler, expectedOutputFiles, extension, key, type, success, chapterCount=-1, fileExt=""):
        zipPath = os.path.join(self.temp_dir, type + ".zip")
        handler.download_file(key, zipPath)
        temp_sub_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix=type + "_")
        unzip(zipPath, temp_sub_dir)

        checkList = []
        if chapterCount <= 0:
            for file in expectedOutputFiles:
                checkList.append(file + "." + extension)
        else:
            checkList = ['{0:0>2}.{1}'.format(i, fileExt) for i in range(1, chapterCount + 1)]

        isFirst = True
        for file in checkList:
            outputFilePath = os.path.join(temp_sub_dir, file)
            print("checking preconvert zip for: " + outputFilePath)
            self.assertTrue(os.path.exists(outputFilePath), "missing file: " + file)
            if isFirst:
                self.printFile(file, outputFilePath)
                isFirst = False

        manifest_json = os.path.join(temp_sub_dir, "manifest.json")
        json_exists = os.path.exists(manifest_json)
        if not success and json_exists: # print out for troubleshooting
            self.printFile("manifest.json", manifest_json)
        manifest_yaml = os.path.join(temp_sub_dir, "manifest.yaml")
        yaml_exists = os.path.exists(manifest_yaml)
        if not success and yaml_exists:  # print out for troubleshooting
            self.printFile("manifest.yaml", manifest_yaml)

        self.assertTrue(json_exists or yaml_exists, "missing manifest file")

    def printFile(self, fileName, filePath):
        text = file_utils.read_file(filePath)
        print("Output file (" + fileName + "): " + text)

    def checkDestinationFiles(self, handler, expectedOutputFiles, extension, key, chapterCount=-1):
        checkList = []
        if chapterCount <= 0:
            for file in expectedOutputFiles:
                checkList.append(file + "." + extension)
        else:
            checkList = ['{0:0>2}.html'.format(i) for i in range(1, chapterCount + 1)]
            # checkList.append("index.html")

        retry_count = 0;
        for file in checkList:
            path = os.path.join(key, file)
            print("checking destination folder for: " + path)
            output = handler.get_file_contents(path)
            while output==None: # try again in a moment since upload files may not be finished
                time.sleep(5)
                retry_count += 1
                if retry_count > 7:
                    print("timeout getting file")
                    break

                print("retry fetch of: " + path)
                output = handler.get_file_contents(path)

            self.assertIsNotNone(output, "missing file: " + path)

        manifest = handler.get_file_contents(os.path.join(key, "manifest.json") )
        if manifest == None:
            manifest = handler.get_file_contents(os.path.join(key, "manifest.yaml") )
        self.assertTrue(len(manifest) > 0, "missing manifest file ")

    def doConversionForRepo(self, baseUrl, user, repo):
        build_log_json = None
        job = None
        success = False
        self.cdn_handler = S3Handler(self.cdn_bucket)
        commitID, commitPath, commitSha = self.fetchCommitDataForRepo(baseUrl, repo, user)  # TODO: change this to use gogs API when finished
        commitLen = len(commitID)
        if commitLen == COMMIT_LENGTH:
            self.deletePreconvertZipFile(commitSha)
            self.deleteTxOutputZipFile(commitID)
            self.emptyDestinationFolder(commitSha, repo, user)
            build_log_json, success, job = self.doConversionJob(baseUrl, commitID, commitPath, commitSha, repo, user)

        return build_log_json, commitID, commitPath, commitSha, success, job

    def emptyDestinationFolder(self, commitSha, repo, user):
        destination_key = self.getDestinationS3Key(commitSha, repo, user)
        for obj in self.cdn_handler.get_objects(prefix=destination_key):
            print("deleting destination file: " + obj.key)
            self.cdn_handler.delete_file(obj.key)

    def deletePreconvertZipFile(self, commitSha):
        self.s3_handler = S3Handler(self.pre_convert_bucket)
        preconvert_key = self.getPreconvertS3Key(commitSha)
        if self.s3_handler.key_exists(preconvert_key):
            print("deleting preconvert file: " + preconvert_key)
            self.s3_handler.delete_file(preconvert_key, catch_exception=True)

    def deleteTxOutputZipFile(self, commitID):
        txOutput_key = self.getTxOutputS3Key(commitID)
        if self.cdn_handler.key_exists(txOutput_key):
            print("deleting tx output file: " + txOutput_key)
            self.cdn_handler.delete_file(txOutput_key, catch_exception=True)

    def getTxOutputS3Key(self, commitID):
        output_key = 'tx/job/{0}.zip'.format(commitID)
        return output_key

    def getDestinationS3Key(self, commitSha, repo, user):
        destination_key = 'u/{0}/{1}/{2}'.format(user, repo, commitSha)
        return destination_key

    def getPreconvertS3Key(self, commitSha):
        preconvert_key = "preconvert/{0}.zip".format(commitSha)
        return preconvert_key

    def doConversionJob(self, baseUrl, commitID, commitPath, commitSha, repo, user):
        gogsUserToken = os.environ.get('GOGS_USER_TOKEN',"")
        if len(gogsUserToken) == 0:
            print("GOGS_USER_TOKEN is missing in environment")

        webhookData = {
            "after": commitID,
            "commits": [
                {
                    "id": "b9278437b27024e07d02490400138d4fd7d1677c",
                    "message": "Fri Dec 16 2016 11:09:07 GMT+0530 (India Standard Time)\n",
                    "url": baseUrl + commitPath,
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
        env_vars = {
            'api_url': self.api_url,
            'pre_convert_bucket': self.pre_convert_bucket,
            'cdn_bucket': self.cdn_bucket,
            'gogs_url': self.gogs_url,
            'gogs_user_token': gogsUserToken,
            'commit_data': webhookData
        }

        if USE_WEB_HOOK_LAMBDA:
            headers = {"content-type": "application/json"}
            tx_client_webhook_url = "{0}/client/webhook".format(self.api_url)
            print('Making request to client/webhook URL {0} with payload:'.format(tx_client_webhook_url), end=' ')
            print(webhookData)
            response = requests.post(tx_client_webhook_url, json=webhookData, headers=headers)
            print('webhook finished with code:' + str(response.status_code))
            print('webhook finished with text:' + str(response.text))
            build_log_json = json.loads(response.text)
            if response.status_code != 200:
                return build_log_json, False, (build_log_json['job_id'])

        else: # do preconvert locally
            try:
                build_log_json = ClientWebhook(**env_vars).process_webhook()
            except Exception as e:
                message = "Exception: " + str(e)
                print(message)
                return None, False, None

        job_id = build_log_json['job_id']
        if job_id == None:
            print("Job ID missing in build_log")
            return None, False, None

        success, job = self.pollUntilJobFinished(job_id)
        build_log_json = self.getJsonFile(commitSha, 'build_log.json', repo, user)
        if build_log_json != None:
            print("Final results:\n" + str(build_log_json))
        return build_log_json, success, job

    def pollUntilJobFinished(self, job_id):
        success = False
        job = None

        env_vars = {
            'api_url': self.api_url,
            'gogs_url': self.gogs_url,
            'cdn_url': self.cdn_url,
            'job_table_name':  self.job_table_name,
            'module_table_name': self.module_table_name,
            'cdn_bucket': self.cdn_bucket
        }
        tx_manager = TxManager(**env_vars)

        pollingTimeout = 5 * 60 # poll for up to 5 minutes for job to complete or error
        sleepInterval = 5 # how often to check for completion
        startMaxWaitCount = 30 / sleepInterval # maximum count to wait for conversion to start (sec/interval)
        for i in range(0, pollingTimeout / sleepInterval):
            job = tx_manager.get_job(job_id)
            self.assertIsNotNone(job)
            print("job status at " + str(i) + ":\n" + str(job.log))

            if job.ended_at != None:
                success = True
                break

            if (i > startMaxWaitCount) and (job.started_at == None):
                success = False
                print("Conversion Failed to start")
                break

            time.sleep(sleepInterval) # delay before polling again

        return success, job

    def getJsonFile(self, commitSha, file, repo, user):
        key = 'u/{0}/{1}/{2}/{3}'.format(user, repo, commitSha, file)
        text = self.cdn_handler.get_json(key)
        return text

    def fetchCommitDataForRepo(self, baseUrl, repo, user):
        commitID = None
        commitSha = None
        commitPath = None
        data = self.readContentsOfRepo(baseUrl, user, repo)
        if len(data) > 10:
            commitID, commitSha, commitPath = self.findLastedCommitFromPage(data)
        return commitID, commitPath, commitSha

    def findLastedCommitFromPage(self, text):
        soup = BeautifulSoup(text, 'html.parser')
        table = soup.find('table')
        commitID = None
        commitSha = None
        commitPath = None
        if table != None:
            rows = table.findAll('tr')
            if (rows != None) and (len(rows) > 0):
                for row in rows:
                    commitCell = row.find('td', {"class": "sha"} )
                    if commitCell != None:
                        commitLink = commitCell.find('a')
                        if commitLink != None:
                            commitPath = commitLink['href']
                            commitSha = self.getContents(commitLink)
                            parts = commitPath.split('/')
                            commitID = parts[4]
                            break

        return commitID, commitSha, commitPath

    def makeFolder(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def readContentsOfRepo(self, baseUrl, user, repo):
        self.url = "{0}/{1}/{2}/commits/master".format(baseUrl, user, repo)
        ttr_response = requests.get(self.url)
        if ttr_response.status_code == 200:
            return ttr_response.text

        print("Failed to load: " + self.url)
        return None

    def getContents(self, item):
        if item != None:
            contents = item.stripped_strings
            for string in contents:
                text = string
                return text
        return None
