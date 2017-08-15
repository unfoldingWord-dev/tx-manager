from __future__ import print_function, unicode_literals
import urlparse
import os
import tempfile
import codecs
from bs4 import BeautifulSoup
from shutil import copyfile
from libraries.general_tools.file_utils import write_file, remove_tree, get_files
from converter import Converter
from usfm_tools.transform import UsfmTransform
from libraries.resource_container.ResourceContainer import BIBLE_RESOURCE_TYPES


class Usfm2HtmlConverter(Converter):

    def convert(self):
        if self.resource in BIBLE_RESOURCE_TYPES:
            self.convert_bible()
            return True
        else:
            return False

    def convert_bible(self):
        self.log.info('Processing the Bible USFM files')

        # find the first directory that has usfm files.
        files = get_files(dir=self.files_dir, exclude=self.EXCLUDED_FILES)

        exclusive_convert = False
        convert_only = []
        if self.source and len(self.source) > 0:
            parsed = urlparse.urlparse(self.source)
            params = urlparse.parse_qsl(parsed.query)
            if params and len(params) > 0:
                for i in range(0, len(params)):
                    item = params[i]
                    if item[0] == 'convert_only':
                        convert_only = item[1].split(',')
                        exclusive_convert = True
                        self.source = urlparse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
                        break

        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'template.html')) as template_file:
            template_html = template_file.read()

        for filename in files:
            if filename.endswith('.usfm'):
                if exclusive_convert:
                    base_name = os.path.basename(filename)
                    if base_name not in convert_only:  # see if this is a file we are to convert
                        continue

                # Covert the USFM file
                scratch_dir = tempfile.mkdtemp(prefix='scratch_')
                copyfile(filename, os.path.join(scratch_dir, os.path.basename(filename)))
                filebase = os.path.splitext(os.path.basename(filename))[0]
                UsfmTransform.buildSingleHtml(scratch_dir, scratch_dir, filebase)
                html_filename = filebase+".html"
                with codecs.open(os.path.join(scratch_dir, html_filename), 'r', 'utf-8-sig') as html_file:
                    converted_html = html_file.read()
                template_soup = BeautifulSoup(template_html, 'html.parser')
                template_soup.head.title.string = self.resource.upper()
                converted_soup = BeautifulSoup(converted_html, 'html.parser')
                content_div = template_soup.find('div', id='content')
                content_div.clear()
                content_div.append(converted_soup.body)
                content_div.body.unwrap()
                output_file = os.path.join(self.output_dir, html_filename)
                write_file(output_file, template_soup.prettify())
                self.log.info('Converted {0} to {1}.'.format(os.path.basename(filename),
                                                             os.path.basename(html_filename)))
                remove_tree(scratch_dir)
            else:
                # Directly copy over files that are not USFM files
                try:
                    output_file = os.path.join(self.output_dir, os.path.basename(filename))
                    if not os.path.exists(output_file):
                        copyfile(filename, output_file)
                except:
                    pass
        self.log.info('Finished processing Bible USFM files.')
