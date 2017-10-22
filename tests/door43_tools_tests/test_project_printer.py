from __future__ import absolute_import, unicode_literals, print_function
import unittest
import os
import tempfile
from moto import mock_s3
from bs4 import BeautifulSoup
from shutil import rmtree
from libraries.door43_tools.project_printer import ProjectPrinter
from libraries.general_tools.file_utils import unzip
from libraries.app.app import App


@mock_s3
class ProjectPrinterTests(unittest.TestCase):
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        App.cdn_s3_handler().create_bucket()
        self.temp_dir = tempfile.mkdtemp(prefix="test_project_printer")
        self.printer = ProjectPrinter()
        self.mock_s3_obs_project()

    def tearDown(self):
        rmtree(self.temp_dir, ignore_errors=True)

    def test_print_obs(self):
        self.printer.print_project(self.project_key)
        self.assertTrue(App.cdn_s3_handler().key_exists('u/{0}/print_all.html'.format(self.project_key)))
        html = App.cdn_s3_handler().get_file_contents('u/{0}/print_all.html'.format(self.project_key))
        soup = BeautifulSoup(html, 'html.parser')
        self.assertEqual(len(soup.div), 69) 
        self.assertEqual(soup.html['lang'], 'en')
        self.assertEqual(soup.html['dir'], 'ltr')
        # Run again, shouldn't have to generate
        self.printer.print_project(self.project_key)
        self.assertTrue(App.cdn_s3_handler().key_exists('u/{0}/print_all.html'.format(self.project_key)))

    def test_random_tests(self):
        self.assertRaises(Exception, self.printer.print_project, 'bad_key')
        self.assertRaises(Exception, self.printer.print_project, 'bad_owner/bad_repo/bad_commit')

    def mock_s3_obs_project(self):
        zip_file = os.path.join(self.resources_dir, 'converted_projects', 'en-obs-complete.zip')
        out_dir = os.path.join(self.temp_dir, 'en-obs-complete')
        unzip(zip_file, out_dir)
        project_dir = os.path.join(out_dir, 'door43', 'en-obs', '12345678')
        self.project_files = [f for f in os.listdir(project_dir) if os.path.isfile(os.path.join(project_dir, f))]
        self.project_key = 'door43/en-obs/12345678'
        for filename in self.project_files:
            App.cdn_s3_handler().upload_file(os.path.join(project_dir, filename), 'u/{0}/{1}'.format(self.project_key, filename))
        App.cdn_s3_handler().upload_file(os.path.join(out_dir, 'door43', 'en-obs', 'project.json'), 'u/door43/en-obs/project.json')

    def test_front_to_back(self):
        file_list = ['01.html', '02.html', 'back.html', 'front.html']
        sorted_file_list = sorted(file_list, key=ProjectPrinter.front_to_back)
        self.assertEqual(sorted_file_list[0], file_list[3])
        self.assertEqual(sorted_file_list[1], file_list[0])
        self.assertEqual(sorted_file_list[2], file_list[1])
        self.assertEqual(sorted_file_list[3], file_list[2])
