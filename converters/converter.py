from __future__ import print_function, unicode_literals
import os
import tempfile
import logging
from logging import Logger
from aws_tools.s3_handler import S3Handler
from general_tools.url_utils import download_file
from general_tools.file_utils import unzip, add_contents_to_zip, remove_tree, copy_tree
from convert_logger import ConvertLogger

class Converter(object):

    def __init__(self, s3_handler_class=S3Handler):
        """
        :param Logger logger:
        :param class s3_handler_class:
        """
        self.logger = ConvertLogger()
        self.s3_handler_class = s3_handler_class

        self.data = {}
        self.options = {}
        self.job = None
        self.source = None
        self.resource = None
        self.cdn_bucket = None
        self.cdn_file = None

        self.download_dir = tempfile.mkdtemp(prefix='download_')
        self.files_dir = tempfile.mkdtemp(prefix='files_')
        self.input_zip_file = None  # If set, won't download the repo archive. Used for testing
        self.output_dir = tempfile.mkdtemp(prefix='output_')
        self.output_zip_file = tempfile.mktemp('.zip')

    def __exit__(self, exc_type, exc_val, exc_tb):
        # delete temp files
        remove_tree(self.download_dir)
        remove_tree(self.files_dir)
        remove_tree(self.output_dir)
        remove_tree(self.output_zip_file)

    def run(self):
        # Custom converters need to add a `convert_<resource>(self)` method for every resource it converts
        convert_method = getattr(self, "convert_{0}".format(self.resource), None)
        if convert_method and callable(convert_method):
            try:
                if not self.input_zip_file or not os.path.exists(self.input_zip_file):
                    # No input zip file yet, so we need to download the archive
                    self.download_archive()
                # unzip the input archive
                unzip(self.input_zip_file, self.files_dir)
                # convert method called
                convert_method()
                # zip the output dir to the output archive
                add_contents_to_zip(self.output_zip_file, self.output_dir)
                # upload the output archive
                self.upload_archive()
            except:
                self.logger.error('Conversion process ended abnormally')
        else:
            self.logger.error('Resource "{0}" not currently supported'.format(self.resource))

        return {
            'status': len(self.logger.logs['error']) == 0,
            'info': self.logger.logs['info'],
            'warnings': self.logger.logs['warning'],
            'errors': self.logger.logs['error']
        }

    def download_archive(self):
        archive_url = self.source
        filename = self.source.rpartition('/')[2]
        self.input_zip_file = os.path.join(self.download_dir, filename)
        if not os.path.isfile(self.input_zip_file):
            try:
                download_file(archive_url, self.input_zip_file)
            finally:
                if not os.path.isfile(self.input_zip_file):
                    raise Exception("Failed to download {0}".format(archive_url))

    def upload_archive(self):
        cdn_handler = self.s3_handler_class(self.cdn_bucket)
        cdn_handler.upload_file(self.output_zip_file, self.cdn_file)

