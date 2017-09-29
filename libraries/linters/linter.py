from __future__ import print_function, unicode_literals
import os
import tempfile
import traceback
import requests
from libraries.general_tools.url_utils import download_file
from libraries.general_tools.file_utils import unzip, remove_tree
from lint_logger import LintLogger
from libraries.resource_container.ResourceContainer import RC
from libraries.app.app import App
from abc import ABCMeta, abstractmethod


class Linter(object):
    __metaclass__ = ABCMeta
    EXCLUDED_FILES = ["license.md", "package.json", "project.json", 'readme.md']

    def __init__(self, source_url=None, source_file=None, source_dir=None, commit_data=None,
                 lint_callback=None, identity=None, cdn_file=None, **kwargs):
        """
        :param string source_url: The main way to give Linter the files via a zip file online
        :param string source_file: If set, will just unzip the local source file
        :param string source_dir: If set, wil just use this directory
        :param dict commit_data: Can get the changes, commit_url, etc from this
        :param string lint_callback: If set, will do callback
        :param string identity: 
        :param string cdn_file:
        :params dict kwargs:
        """
        self.source_url = source_url
        self.source_file = source_file
        self.source_dir = source_dir
        self.commit_data = commit_data

        self.log = LintLogger()

        self.temp_dir = tempfile.mkdtemp(prefix='tmp_lint_')

        self.repo_owner = ''
        self.repo_name = ''
        if self.commit_data:
            self.repo_name = self.commit_data['repository']['name']
            self.repo_owner = self.commit_data['repository']['owner']['username']
        self.rc = None   # Constructed later when we know we have a source_dir

        self.callback = lint_callback
        self.callback_status = 0
        self.callback_results = None
        self.identity = identity
        if self.callback and not identity:
            App.logger.error("Identity not given for callback")
        self.s3_results_key = cdn_file
        if self.callback and not cdn_file:
            App.logger.error("s3_results_key not given for callback")

    def close(self):
        """delete temp files"""
        remove_tree(self.temp_dir)

    def __del__(self):
        self.close()

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
        success = False
        try:
            # Download file if a source_zip_url was given
            if self.source_url:
                App.logger.debug("Linting url: " + self.source_url)
                self.download_archive()
            # unzip the input archive if a source_zip_file exists
            if self.source_file:
                App.logger.debug("Linting zip: " + self.source_file)
                self.unzip_archive()
            # lint files
            if self.source_dir:
                self.rc = RC(directory=self.source_dir)
                App.logger.debug("Linting '{0}' files...".format(self.source_dir))
                success = self.lint()
                App.logger.debug("...finished.")
        except Exception as e:
            message = 'Linting process ended abnormally: {0}'.format(e.message)
            App.logger.error(message)
            self.log.warnings.append(message)
            App.logger.error('{0}: {1}'.format(str(e), traceback.format_exc()))
        results = {
            'identity': self.identity,
            'success': success,
            'warnings': self.log.warnings,
        }

        if self.callback is not None:
            self.callback_results = results
            self.do_callback(self.callback, self.callback_results)

        App.logger.debug("Linter results: " + str(results))
        return results

    def download_archive(self):
        filename = self.source_url.rpartition('/')[2]
        self.source_file = os.path.join(self.temp_dir, filename)
        App.logger.debug("Downloading {0} to {1}".format(self.source_url, self.source_file))
        if not os.path.isfile(self.source_file):
            try:
                download_file(self.source_url, self.source_file)
            finally:
                if not os.path.isfile(self.source_file):
                    raise Exception("Failed to download {0}".format(self.source_url))

    def unzip_archive(self):
        App.logger.debug("Unzipping {0} to {1}".format(self.source_file, self.temp_dir))
        unzip(self.source_file, self.temp_dir)
        dirs = [d for d in os.listdir(self.temp_dir) if os.path.isdir(os.path.join(self.temp_dir, d))]
        if len(dirs):
            self.source_dir = os.path.join(self.temp_dir, dirs[0])
        else:
            self.source_dir = self.temp_dir

    def do_callback(self, url, payload):
        if url.startswith('http'):
            headers = {"content-type": "application/json"}
            App.logger.debug('Making callback to {0} with payload:'.format(url))
            App.logger.debug(payload)
            response = requests.post(url, json=payload, headers=headers)
            self.callback_status = response.status_code
            if (self.callback_status >= 200) and (self.callback_status < 299):
                App.logger.debug('finished.')
            else:
                App.logger.error('Error calling callback code {0}: {1}'.format(self.callback_status, response.reason))
        else:
            App.logger.error('Invalid callback url: {0}'.format(url))
