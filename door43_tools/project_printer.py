from __future__ import print_function, unicode_literals
import os
import tempfile
import codecs
from bs4 import BeautifulSoup
from glob import glob
from general_tools.file_utils import load_json_object
from aws_tools.s3_handler import S3Handler
from manifest_handler import Manifest


class ProjectPrinter(object):
    """
    Prints a project given the project ID

    Read from the project's dir in the cdn.door43.org bucket all the .html file and compile them into one for printing,
    if the print_all.html page doesn't already exist. Return the contents of print_all.html
    """

    def __init__(self, cdn_bucket):
        """
        :param string cdn_bucket: 
        :param string cdn_url:
        """
        self.cdn_bucket = cdn_bucket
        self.cdn_handler = None
        self.setup_resources()

    def setup_resources(self):
        self.cdn_handler = S3Handler(self.cdn_bucket)

    def print_project(self, project_id):
        """
        :param string project_id: 
        :return string: 
        """
        if len(project_id.split('/')) != 3:
            raise Exception('Project not found.')
        owner_name, repo_name, commit_id = project_id.split('/')
        source_path = 'u/{0}'.format(project_id)
        print_all_key = '{0}/print_all.html'.format(source_path)
        print_all_file = tempfile.mktemp(prefix='print_all')
        if not self.cdn_handler.key_exists(print_all_key):
            files_dir = tempfile.mkdtemp(prefix='files_')
            project_dir = files_dir, source_path.replace('/', os.path.sep)
            self.cdn_handler.download_dir(source_path, files_dir)
            manifest_filename = os.path.join(project_dir, 'manifest.json')
            manifest = Manifest(file_name=manifest_filename, repo_name=repo_name, files_path=project_dir)
            if manifest.resource['name']:
                name = manifest.resource['name']
            else:
                name = repo_name
            with codecs.open(print_all_file, 'w', 'utf-8-sig') as print_all:
                print_all.write('<html><head><title>{0}></title></head><body><h1>{0}</h1>'.format(name))
                for fname in sorted(glob(os.path.join(project_dir, '*.html'))):
                    with codecs.open(fname, 'r', 'utf-8-sig') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                        # get the body of the raw html file
                        content = soup.div
                        if not content:
                            content = BeautifulSoup('<div>No content</div>', 'html.parser').find('div').extract()
                        content['id'] = os.path.basename(fname)
                        content.attrs['style'] = 'page-break-after: always; '
                        print_all.write(unicode(content))
                print_all.write('</body></html>')
            self.cdn_handler.upload_file(print_all_file, print_all_key)
