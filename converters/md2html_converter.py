from __future__ import print_function, unicode_literals
import os
import string
import markdown
import codecs
from glob import glob
from shutil import copyfile
from general_tools.file_utils import write_file
from converter import Converter
from door43_tools.obs_handler import OBSInspection


class Md2HtmlConverter(Converter):

    def convert_obs(self):
        self.logger.info('Processing the OBS markdown files')

        # find the first directory that has md files.
        files = self.get_files()

        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'obs-template.html')) as template_file:
            html_template = string.Template(template_file.read())

        for filename in files:
            if filename.endswith('.md'):
                # Convert files tat are markdown files
                with codecs.open(filename, 'r', 'utf-8-sig') as md_file:
                    md = md_file.read()
                html = markdown.markdown(md)
                html = html_template.safe_substitute(content=html)
                base_name = os.path.splitext(os.path.basename(filename))[0]
                html_filename = base_name + ".html"
                output_file = os.path.join(self.output_dir, html_filename)
                write_file(output_file, html)
                self.logger.info('Converted {0} to {1}.'.format(os.path.basename(filename), os.path.basename(html_filename)))

                # Do the OBS inspection (this now operates on a single file instead of folder)
                # QUESTION: Should this be done separately after conversion????
                inspector = OBSInspection(output_file)
                try:
                    inspector.run()
                except Exception as e:
                    self.logger.warning('Chapter {0}: failed to run OBS inspector: {1}'.format(base_name, e.message))
            else:
                # Directly copy over files that are not markdown files
                try:
                    output_file = os.path.join(self.output_dir, filename[len(self.files_dir)+1:])
                    if not os.path.exists(output_file):
                        if not os.path.exists(os.path.dirname(output_file)):
                            os.makedirs(os.path.dirname(output_file))
                        copyfile(filename, output_file)
                except Exception:
                    pass
        self.logger.info('Finished processing Markdown files.')
