from __future__ import print_function, unicode_literals
import os
import tempfile
import codecs
from bs4 import BeautifulSoup
from glob import glob
from aws_tools.s3_handler import S3Handler
from general_tools.file_utils import read_file
from resource_container.ResourceContainer import RC


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
        print_all_file = tempfile.mktemp(prefix='print_all_')
        if not self.cdn_handler.key_exists(print_all_key):
            files_dir = tempfile.mkdtemp(prefix='files_')
            self.cdn_handler.download_dir(source_path, files_dir)
            project_dir = os.path.join(files_dir, source_path.replace('/', os.path.sep))
            if not os.path.isdir(project_dir):
                raise Exception('Project not found.')
            rc = RC(project_dir, repo_name)
            with codecs.open(print_all_file, 'w', 'utf-8-sig') as print_all:
                print_all.write("""
<html lang="{0}" dir="{1}>
    <head>
        <meta charset="UTF-8">
        <title>{2}: {3}</title>
        <style type="text/css">
            body > div {{
                page-break-after: always;
            }}
        </style>
    </head>
    <body onload="window.print()">
        <h1>{2}: {3}</h1>
""".format(rc.resource.language.identifier, rc.resource.language.direction, rc.resource.language.title, rc.resource.title))
                for fname in sorted(glob(os.path.join(project_dir, '*.html'))):
                    with codecs.open(fname, 'r', 'utf-8-sig') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                        # get the body of the raw html file
                        content = soup.div
                        if not content:
                            content = BeautifulSoup('<div>No content</div>', 'html.parser').find('div').extract()
                        content['id'] = os.path.basename(fname)
                        print_all.write(unicode(content))
                print_all.write("""
    </body>
</html>
""")
                self.cdn_handler.upload_file(print_all_file, print_all_key)
            html = read_file(print_all_file)
        else:
            html = self.cdn_handler.get_file_contents(print_all_key)
        return html
