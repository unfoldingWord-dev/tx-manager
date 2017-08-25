from __future__ import print_function, unicode_literals
import os
import tempfile
from libraries.general_tools.url_utils import download_file
from libraries.general_tools.file_utils import unzip, remove_tree, remove
import logging
from lint_logger import LintLogger
from libraries.resource_container.ResourceContainer import RC
from abc import ABCMeta, abstractmethod


class Linter(object):
    __metaclass__ = ABCMeta
    EXCLUDED_FILES = ["license.md", "package.json", "project.json", 'readme.md']

    def __init__(self, source_zip_url=None, source_zip_file=None, source_dir=None, rc=None, commit_data=None, prefix='', **kwargs):
        """
        :param string source_zip_url: The main way to give Linter the files
        :param string source_zip_file: If set, will just unzip this local file
        :param string source_dir: If set, wil just use this directory
        :param RC rc: Can get the language code, resource id, file_ext, etc. from this
        :param dict commit_data: Can get the changes, commit_url, etc from this
        :param string prefix: For calling the node.js Markdown linter Lambda function in different environments
        :param dict **kwawrgs: So other arguments can be passed and be ignored
        """
        self.source_zip_url = source_zip_url
        self.source_zip_file = source_zip_file
        self.source_dir = source_dir
        self.rc = rc
        self.commit_data = commit_data
        self.prefix = prefix

        self.logger = logging.getLogger('linter')
        self.logger.addHandler(logging.NullHandler())
        self.log = LintLogger()

        self.temp_dir = tempfile.mkdtemp(prefix='tmp_lint_')

        self.repo_owner = ''
        self.repo_name = ''
        if commit_data:
            self.repo_name = self.commit_data['repository']['name']
            self.repo_owner = self.commit_data['repository']['owner']['username']

    def __del__(self):
        """delete temp files"""
        remove_tree(self.temp_dir)

    @abstractmethod
    def lint(self):
        """
        Dummy function for linters.

        Returns true if it was able to lint the files
        :return bool:
        """
        raise NotImplementedError()

    def run(self):
        """
        Run common handling for all linters,and then calls the lint() function
        """
        try:
            # Download file if a source_zip_url was given
            if self.source_zip_url:
                self.logger.debug("Linting url: " + self.source_zip_url)
                self.download_archive()
            # unzip the input archive if a source_zip_file exists
            if self.source_zip_file:
                self.logger.debug("Linting zip: " + self.source_zip_file)
                self.unzip_archive()
            # lint files
            if self.source_dir:
                self.logger.debug("Linting {0} files...".format(self.source_dir))
                success = self.lint()
                self.logger.debug("...finished.")
        except Exception as e:
            message = 'Linting process ended abnormally: {0}'.format(e.message)
            self.logger.error(message)
            self.log.warnings.append(message)
            success = False
        result = {
            'success': success,
            'warnings': self.log.warnings,
        }
        self.logger.debug("Linter results: " + str(result))
        return result

    def download_archive(self):
        filename = self.source_zip_url.rpartition('/')[2]
        self.source_zip_file = os.path.join(self.temp_dir, filename)
        self.logger.debug("Downloading {0} to {1}".format(self.source_zip_url, self.source_zip_file))
        if not os.path.isfile(self.source_zip_file):
            try:
                download_file(self.source_zip_url, self.source_zip_file)
            finally:
                if not os.path.isfile(self.source_zip_file):
                    raise Exception("Failed to download {0}".format(self.source_zip_url))

    def unzip_archive(self):
        self.logger.debug("Unzipping {0} to {1}".format(self.source_zip_file, self.temp_dir))
        unzip(self.source_zip_file, self.temp_dir)
        dirs = [d for d in os.listdir(self.temp_dir) if os.path.isdir(os.path.join(self.temp_dir, d))]
        if len(dirs):
            self.source_dir = os.path.join(self.temp_dir, dirs[0])
        else:
            self.source_dir = self.temp_dir
