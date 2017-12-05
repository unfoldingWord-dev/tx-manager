from __future__ import print_function, unicode_literals
import urlparse
import os
import tempfile
import codecs
from bs4 import BeautifulSoup
from shutil import copyfile
from libraries.app.app import App
from libraries.general_tools.file_utils import write_file, remove_tree, get_files
from converter import Converter
from usfm_tools.transform import UsfmTransform


class Usfm2HtmlConverter(Converter):


    def convert(self):
        App.logger.debug('Processing the Bible USFM files')

        # find the first directory that has usfm files.
        files = get_files(directory=self.files_dir, exclude=self.EXCLUDED_FILES)
        convert_only_list = self.check_for_exclusive_convert()

        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'template.html')) as template_file:
            template_html = template_file.read()

        for filename in files:
            if filename.endswith('.usfm'):
                base_name = os.path.basename(filename)
                if convert_only_list and (base_name not in convert_only_list):  # see if this is a file we are to convert
                    continue

                msg = 'Converting Bible USFM file: {0}'.format(base_name)
                self.log.info(msg)
                App.logger.debug(msg)

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
                if converted_soup and converted_soup.body:
                    content_div.append(converted_soup.body)
                    content_div.body.unwrap()
                else:
                    content_div.append('<div class="error">ERROR! NOT CONVERTED!</div>')
                output_file = os.path.join(self.output_dir, html_filename)
                write_file(output_file, unicode(template_soup))
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
        return True
