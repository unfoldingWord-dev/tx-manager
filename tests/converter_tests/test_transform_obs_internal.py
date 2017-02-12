from __future__ import absolute_import, unicode_literals, print_function
import unittest
import codecs
import os
import shutil
import tempfile
import zipfile
from contextlib import closing
import pkg_resources
from bs4 import BeautifulSoup
from functions.convert.transform_obs import TransformOBS
from general_tools.file_utils import unzip, add_file_to_zip
from door43_tools.obs_handler import OBSInspection
from door43_tools.manifest_handler import MetaData, Manifest
from door43_tools.preprocessors import TsObsMarkdownPreprocessor


# test Transform OBS from md to html using external url

class Version(object):
    @classmethod
    def atLeast(cls, package, minimum_version):  # returns true if
        pkg_version = cls.packageVersion(package)
        satisfies_minimum = pkg_resources.parse_version(pkg_version) >= pkg_resources.parse_version(minimum_version) if pkg_version else False
        print("Version requirements satisfied: {0}".format(satisfies_minimum))
        return satisfies_minimum

    @classmethod
    def packageVersion(cls, package):
        try:
            pkg_version = pkg_resources.get_distribution(package).version
            print("Found version for '{0}': {1}".format(package, pkg_version))
            return pkg_version
        except:
            print("Could not find version for '{0}'".format(package))
            return None


class TestTransformOBSInternal(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    version_tx_shared = Version.packageVersion("tx-shared_tools")

    def setUp(self):
        """
        Runs before each test
        """
        self.out_dir = ''
        self.temp_dir = ""
        self.temp_dir2 = ""

    def tearDown(self):
        """
        Runs after each test
        """
        # delete temp files
        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir, ignore_errors=True)
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        if os.path.isdir(self.temp_dir2):
            shutil.rmtree(self.temp_dir2, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        """
        Called before tests in this class are run
        """
        pass

    @classmethod
    def tearDownClass(cls):
        """
        Called after tests in this class are run
        """
        pass


    def test_close(self):
        """
        This tests that the temp directories are deleted when the class is closed
        """

        with closing(TransformOBS('', '', True)) as tx:
            download_dir = tx.download_dir
            files_dir = tx.files_dir

            # verify the directories are present
            self.assertTrue(os.path.isdir(download_dir))
            self.assertTrue(os.path.isdir(files_dir))

        # now they should have been deleted
        self.assertFalse(os.path.isdir(download_dir))
        self.assertFalse(os.path.isdir(files_dir))


    @unittest.skipUnless(Version.atLeast("tx-manager", '0.2.0'), "not supported in this library version")
    def test_completeMD(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'markdown_sources/aab_obs_text_obs.zip'
        expected_warnings = 0
        expected_errors= 0
        zip_filepath = os.path.join(self.resources_dir, file_name)

        # when
        tx = self.doTransformObs(zip_filepath)

        #then
        self.verifyTransform(expected_errors, expected_warnings, tx)


    @unittest.skipUnless(Version.atLeast("tx-manager", '0.2.0'), "not supported in this library version")
    def test_missing_chapterMD(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'markdown_sources/aab_obs_text_obs-missing_chapter_01.zip'
        expected_warnings = 0
        expected_errors= 0
        missing_chapters = [1]
        zip_filepath = os.path.join(self.resources_dir, file_name)

        # when
        tx = self.doTransformObs(zip_filepath)

        #then
        self.verifyTransform(expected_errors, expected_warnings, tx, missing_chapters)


    @unittest.skipUnless(Version.atLeast("tx-manager", '0.2.0'), "not supported in this library version")
    def test_complete(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'aab_obs_text_obs.zip'
        repo_name = 'aab_obs_text_obs'
        expected_warnings = 0
        expected_errors= 0
        zip_filepath = self.preprocessOBS(repo_name, file_name)

        # when
        tx = self.doTransformObs(zip_filepath)

        #then
        self.verifyTransform(expected_errors, expected_warnings, tx)


    @unittest.skipUnless(Version.atLeast("tx-manager", '0.2.0'), "not supported in this library version")
    def test_missing_fragment(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'aab_obs_text_obs_missing_fragment_01_01.zip'
        repo_name = 'aab_obs_text_obs'
        expected_warnings = 1
        expected_errors= 0
        zip_filepath = self.preprocessOBS(repo_name, file_name)

        # when
        tx = self.doTransformObs(zip_filepath)

        #then
        self.verifyTransform(expected_errors, expected_warnings, tx)


    @unittest.skipUnless(Version.atLeast("tx-manager", '0.2.0'), "not supported in this library version")
    def test_missing_chapter(self):
        """
        Runs the converter and verifies the output
        """

        # given
        file_name = 'aab_obs_text_obs-missing_chapter_01.zip'
        repo_name = 'aab_obs_text_obs'
        expected_warnings = 0
        expected_errors= 0
        missing_chapters = [1]
        zip_filepath = self.preprocessOBS(repo_name, file_name)

        # when
        tx = self.doTransformObs(zip_filepath)

        #then
        self.verifyTransform(expected_errors, expected_warnings, tx, missing_chapters)


    def verifyTransform(self, expected_errors, expected_warnings, tx, missing_chapters = []):
        # 07 JAN 2017, NB: currently just one html file is being output, all.html
        files_to_verify = []
        files_missing = []
        for i in range(1, 51):
            file_name = str(i).zfill(2) + '.html'
            if not i in missing_chapters:
                files_to_verify.append(file_name)
            else:
                files_missing.append(file_name)

        for file_to_verify in files_to_verify:
            file_path = os.path.join(self.out_dir, file_to_verify)
            contents = self.getContents(file_path)
            self.assertIsNotNone(contents, 'OBS HTML body contents not found: {0}'.format(os.path.basename(file_path)))

        for file_to_verify in files_missing:
            file_path = os.path.join(self.out_dir, file_to_verify)
            contents = self.getContents(file_path)
            self.assertIsNone(contents, 'OBS HTML body contents present, but should not be: {0}'.format(os.path.basename(file_path)))

        for warning in tx.warnings:
            print("Warning: " + warning)
        for error in tx.errors:
            print("Error: " + error)
        self.assertEqual(len(tx.warnings), expected_warnings)
        self.assertEqual(len(tx.errors), expected_errors)


    def getContents(self, file_path):
        if not os.path.isfile(file_path):
            return None

        with codecs.open(file_path, 'r', 'utf-8-sig') as f:
            soup = BeautifulSoup(f, 'html.parser')

        body = soup.find('body')
        if not body:
            return None

        content = body.find(id='content')
        if not content:
            return None

        return content


    def doTransformObs(self, zip_filepath):
        self.out_dir = tempfile.mkdtemp(prefix='txOBS_Test_')
        with closing(TransformOBS(None, self.out_dir, True)) as tx:
            tx.run(zip_filepath)
        return tx

    @classmethod
    def add_contents_to_zip(cls, zip_file, path):
        """
        Zip the contents of <path> into <zip_file>.
        :param str|unicode zip_file: The file name of the zip file
        :param str|unicode path: Full path of the directory to zip up
        """
        path = path.rstrip(os.sep)
        with zipfile.ZipFile(zip_file, 'a') as zf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zf.write(file_path, file_path[len(path)+1:])

    def preprocessOBS(self, repo_name, file_name): # emulates the preprocessing of the raw files

        file_path = os.path.join(self.resources_dir, file_name)

        # 1) unzip the repo files
        self.temp_dir = tempfile.mkdtemp(prefix='repo_')
        unzip(file_path, self.temp_dir)
        repo_dir = os.path.join(self.temp_dir, repo_name)
        if not os.path.isdir(repo_dir):
            repo_dir = file_path

        # 2) Get the manifest file or make one if it doesn't exist based on meta.json, repo_name and file extensions
        manifest_path = os.path.join(repo_dir, 'manifest.json')
        if not os.path.isfile(manifest_path):
            manifest_path = os.path.join(repo_dir, 'project.json')
            if not os.path.isfile(manifest_path):
                manifest_path = None
        meta_path = os.path.join(repo_dir, 'meta.json')
        meta = None
        if os.path.isfile(meta_path):
            meta = MetaData(meta_path)
        manifest = Manifest(file_name=manifest_path, repo_name=repo_name, files_path=repo_dir, meta=meta)

        # run OBS Preprocessor
        self.temp_dir2 = tempfile.mkdtemp(prefix='output_')
        compiler = TsObsMarkdownPreprocessor(manifest, repo_dir, self.temp_dir2)
        compiler.run()

        # 3) Zip up the massaged files
        # context.aws_request_id is a unique ID for this lambda call, so using it to not conflict with other requests
        zip_filename = 'preprocessed.zip'
        zip_filepath = os.path.join(self.temp_dir, zip_filename)
        self.add_contents_to_zip(zip_filepath, self.temp_dir2)
        if os.path.isfile(manifest_path) and not os.path.isfile(os.path.join(self.temp_dir2, 'manifest.json')):
            add_file_to_zip(zip_filepath, manifest_path, 'manifest.json')

        return zip_filepath

    def packageFiles(self, repo_name, file_name): # emulates the preprocessing of the raw files
        file_path = os.path.join(self.resources_dir, file_name)
        self.temp_dir = tempfile.mkdtemp(prefix='repo_')

        zip_filename = 'preprocessed.zip'
        zip_filepath = os.path.join(self.temp_dir, zip_filename)
        self.add_contents_to_zip(zip_filepath, file_path)

        return zip_filepath


    # def test_PackageResource(self):
    #
    #     #given
    #     resource = 'markdown_sources'
    #     repo_name = 'aab_obs_text_obs-missing_chapter_01'
    #
    #     # when
    #     zip_file = self.packageResource(resource, repo_name)
    #
    #     #then
    #     print(zip_file)


    @classmethod
    def createZipFile(cls, zip_filename, destination_folder, source_folder):
        zip_filepath = os.path.join(destination_folder, zip_filename)
        cls. add_contents_to_zip(zip_filepath, source_folder)
        return zip_filepath

    def packageResource(self, resource, repo_name):
        source_folder = os.path.join(self.resources_dir, resource, repo_name)
        self.temp_dir = tempfile.mkdtemp(prefix='repo_')
        zip_filepath = self.createZipFile(repo_name + ".zip", self.temp_dir, source_folder)
        return zip_filepath


if __name__ == '__main__':
    unittest.main()

