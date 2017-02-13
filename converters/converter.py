from __future__ import print_function, unicode_literals
import os
import tempfile
import logging
from logging import Logger
from aws_tools.s3_handler import S3Handler
from shutil import rmtree
from general_tools.url_utils import download_file
from general_tools.file_utils import unzip, add_contents_to_zip


class Converter(object):

    def __init__(self, logger, s3_handler_class=S3Handler):
        """
        :param Logger logger:
        :param class s3_handler_class:
        """
        self.logger = logger
        self.s3_handler_class = s3_handler_class

        self.convert_log = logging.getLogger('convert_log')
        self.convert_log.setLevel(logging.INFO)
        logging.raiseExceptions = 1

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

    def close(self):
        # delete temp files
        if os.path.isdir(self.download_dir):
            rmtree(self.download_dir, ignore_errors=True)
        if os.path.isdir(self.files_dir):
            rmtree(self.files_dir, ignore_errors=True)
        if os.path.isdir(self.output_dir):
            rmtree(self.output_dir, ignore_errors=True)
        if os.path.isfile(self.output_zip_file):
            os.remove(self.output_zip_file)
        logging.raiseExceptions = 1

    def run(self):
        # Custom converters need to add a `convert_<resource>(self)` method for every resource it converts
        convert_method = getattr(self, "convert_{0}".format(self.resource), None)
        if convert_method and callable(convert_method):
            try:
                if not self.input_zip_file or not os.path.exists(self.input_zip_file):
                    # No input zip file yet, so we need to download the archive
                    self.download_archive()

                # unzip the input archive
                self.logger.info('Unzipping {0}...'.format(self.input_zip_file))
                unzip(self.input_zip_file, self.files_dir)
                self.logger.info('Unzip successful.')

                # convert method called
                convert_method()

                # zip the output dir to the output archive
                add_contents_to_zip(self.output_zip_file, self.output_dir)

                # upload the output archive
                self.upload_archive()
            except Exception as e:
                self.convert_log.error('Conversion process ended abnormally')
                self.logger.exception(e)
        else:
            message = 'Resource "{0}" not currently supported'.format(self.resource)
            self.convert_log.error(message)
            self.logger.error(message)

        return {'status':'need results'}

    def download_archive(self):
        archive_url = self.source
        filename = self.source.rpartition('/')[2]
        self.input_zip_file = os.path.join(self.download_dir, filename)
        self.logger.info('Downloading {0}...'.format(archive_url))
        if not os.path.isfile(self.input_zip_file):
            try:
                download_file(archive_url, self.input_zip_file)
            finally:
                if not os.path.isfile(self.input_zip_file):
                    self.logger.error("Failed to download {0}".format(archive_url))
                else:
                    self.logger.info('Download successful.')

    def upload_archive(self):
        self.logger.info("Uploading {0} to {1}/{2}".format(os.path.basename(self.output_zip_file), self.cdn_bucket, self.cdn_file))
        cdn_handler = self.s3_handler_class(self.cdn_bucket)
        cdn_handler.upload_file(self.output_zip_file, self.cdn_file)
        self.logger.info("Upload successful.")

