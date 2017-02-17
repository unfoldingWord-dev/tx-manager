from __future__ import print_function, unicode_literals
import os
import tempfile
from aws_tools.s3_handler import S3Handler
from general_tools.url_utils import download_file
from general_tools.file_utils import unzip, add_contents_to_zip, remove_tree, remove
from shutil import copy
from convert_logger import ConvertLogger


class Converter(object):

    EXCLUDED_FILES = ["license.md", "manifest.json", "package.json", "project.json", 'readme.md']

    def __init__(self, source, resource, cdn_bucket=None, cdn_file=None, options=None):
        self.logger = ConvertLogger()
        self.options = {}
        self.source = source
        self.resource = resource
        self.cdn_bucket = cdn_bucket
        self.cdn_file = cdn_file
        self.options = options

        if not self.options:
            self.options = {}

        self.download_dir = tempfile.mkdtemp(prefix='download_')
        self.files_dir = tempfile.mkdtemp(prefix='files_')
        self.input_zip_file = None  # If set, won't download the repo archive. Used for testing
        self.output_dir = tempfile.mkdtemp(prefix='output_')
        self.output_zip_file = tempfile.mktemp(prefix="{0}_".format(resource), suffix='.zip')

    def close(self):
        # delete temp files
        remove_tree(self.download_dir)
        remove_tree(self.files_dir)
        remove_tree(self.output_dir)
        remove(self.output_zip_file)

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
                # upload the output archive either to cdn_bucket or to a file (no cdn_bucket)
                self.upload_archive()
            except Exception as e:
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
        if self.cdn_bucket:
            cdn_handler = S3Handler(self.cdn_bucket)
            cdn_handler.upload_file(self.output_zip_file, self.cdn_file)
        elif self.cdn_file and os.path.isdir(os.path.dirname(self.cdn_file)):
            copy(self.output_zip_file, self.cdn_file)

    def get_files(self):
        files = []
        for root, dirs, filenames in os.walk(self.files_dir):
            for filename in filenames:
                if filename.lower() not in Converter.EXCLUDED_FILES:
                    filepath = os.path.join(root, filename)
                    files.append(filepath)
        return files
