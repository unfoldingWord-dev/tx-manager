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

    def __init__(self, source, rc=None, commit_data=None, prefix='', **kwargs):
        """
        :param string source:
        :param RC rc: Can get the language code, resource id, file_ext, etc. from this
        :param dict commit_data: Can get the changes, commit_url, etc from this
        :param string prefix: For calling the node.js Markdown linter Lambda function in different environments
        :param dict **kwawrgs: So other arguments can be passed and be ignored
        """
        self.source = source
        self.rc = rc
        self.commit_data = commit_data
        self.prefix = prefix

        self.logger = logging.getLogger('linter')
        self.logger.addHandler(logging.NullHandler())
        self.log = LintLogger()

        self.temp_dir = tempfile.mkdtemp(prefix='tmp_lint_')
        self.source_dir = None  # Will be populated with the repo name
        self.source_zip_file = None  # If set, won't download the repo archive. Used for testing

        self.repo_owner = ''
        self.repo_name = ''
        if commit_data:
            self.repo_name = self.commit_data['repository']['name']
            self.repo_owner = self.commit_data['repository']['owner']['username']

    def close(self):
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
            if not self.source_zip_file:
                # No input zip file yet, so we need to download the archive
                self.download_archive()
            # unzip the input archive
            self.logger.debug("Unzipping {0} to {1}".format(self.source_zip_file, self.temp_dir))
            unzip(self.source_zip_file, self.temp_dir)
            dirs = [d for d in os.listdir(self.temp_dir) if os.path.isdir(os.path.join(self.temp_dir, d))]
            if len(dirs):
                self.source_dir = os.path.join(self.temp_dir, dirs[0])
            else:
                self.source_dir = self.temp_dir
            # convert method called
            self.logger.debug("Linting files...")
            success = self.lint()
            self.logger.debug("...finished.")
        except Exception as e:
            self.logger.error('Linting process ended abnormally: {0}'.format(e.message))
            success = False
        result = {
            'success': success,
            'warnings': self.log.warnings,
        }
        return result

    def download_archive(self):
        archive_url = self.source
        filename = self.source.rpartition('/')[2]
        self.source_zip_file = os.path.join(self.temp_dir, filename)
        if not os.path.isfile(self.source_zip_file):
            try:
                download_file(archive_url, self.source_zip_file)
            finally:
                if not os.path.isfile(self.source_zip_file):
                    raise Exception("Failed to download {0}".format(archive_url))
