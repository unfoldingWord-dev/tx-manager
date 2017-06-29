from __future__ import print_function, unicode_literals
import os
import tempfile
import codecs
from bs4 import BeautifulSoup
from shutil import copyfile
from general_tools.file_utils import write_file, remove_tree
from converter import Converter
from usfm_tools.transform import UsfmTransform


class Usfm2HtmlConverter(Converter):

    def convert(self):
        if self.resource in ['ulb', 'udb', 'bible', 'reg']:
            self.convert_bible()
            return True
        else:
            return False

    def convert_bible(self):
        self.log.info('Processing the Bible USFM files')

        # find the first directory that has usfm files.
        files = self.get_files()

        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'bible-template.html')) as template_file:
            template_html = template_file.read()

        for filename in files:
            if filename.endswith('.usfm'):
                # Covert the USFM file
                scratch_dir = tempfile.mkdtemp(prefix='scratch_')
                copyfile(filename, os.path.join(scratch_dir, os.path.basename(filename)))
                filebase = os.path.splitext(os.path.basename(filename))[0]
                UsfmTransform.buildSingleHtml(scratch_dir, scratch_dir, filebase)
                html_filename = filebase+".html"
                with codecs.open(os.path.join(scratch_dir, html_filename), 'r', 'utf-8-sig') as html_file:
                    converted_html = html_file.read()
                template_soup = BeautifulSoup(template_html, 'html.parser')
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

                # TODO 3/30/17 BLM - should be an inspection here like OBS has?

            else:
                # Directly copy over files that are not USFM files
                try:
                    output_file = os.path.join(self.output_dir, os.path.basename(filename))
                    if not os.path.exists(output_file):
                        copyfile(filename, output_file)
                except:
                    pass

        # Do the Bible inspection HERE
        #        inspector = BibleInspection(self.output_dir, self.log)
        #        inspector.run()
        #        complete_html = html_template.safe_substitute(content=complete_html)
        #        write_file(os.path.join(self.output_dir, 'all.html'), complete_html)
        #        self.log_message('Made one HTML of all bibles in all.html.')
        #        self.log_message('Finished processing Markdown files.')
        self.log.info('Finished processing Bible USFM files.')
