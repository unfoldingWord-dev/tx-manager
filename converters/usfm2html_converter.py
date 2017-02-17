from __future__ import print_function, unicode_literals
import os
import tempfile
import string
import codecs
from shutil import copyfile
from general_tools.file_utils import write_file, remove_tree
from converter import Converter
from usfm_tools.transform import UsfmTransform

class Usfm2HtmlConverter(Converter):

    def convert_udb(self):
        self.convert_bible()

    def convert_ulb(self):
        self.convert_bible()

    def convert_bible(self):
        self.logger.info('Processing the Bible USFM files')

        # find the first directory that has usfm files.
        files = self.get_files()

        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'bible-template.html')) as template_file:
            html_template = string.Template(template_file.read())

        complete_html = ''
        for filename in files:
            if filename.endswith('.usfm'):
                # Covert the USFM file
                scratch_dir = tempfile.mkdtemp(prefix='scratch_')
                copyfile(filename, os.path.join(scratch_dir, os.path.basename(filename)))
                filebase = os.path.splitext(os.path.basename(filename))[0]
                UsfmTransform.buildSingleHtml(scratch_dir, scratch_dir, filebase)
                html_filename = filebase+".html"
                with codecs.open(os.path.join(scratch_dir, html_filename), 'r', 'utf-8-sig') as html_file:
                    html = html_file.read()
                complete_html += html
                html = html_template.safe_substitute(content=html)
                output_file = os.path.join(self.output_dir, html_filename)
                write_file(output_file, html)
                self.logger.info('Converted {0} to {1}.'.format(os.path.basename(filename),
                                                                os.path.basename(html_filename)))
                remove_tree(scratch_dir)
            else:
                # Directly copy over files that are not USFM files
                try:
                    output_file = os.path.join(self.output_dir, filename[len(self.files_dir)+1:])
                    if not os.path.exists(output_file):
                        if not os.path.exists(os.path.dirname(output_file)):
                            os.makedirs(os.path.dirname(output_file))
                        copyfile(filename, output_file)
                except Exception:
                    pass

        manifest_file = os.path.join(self.files_dir, 'manifest.json')
        if os.path.isfile(manifest_file):
            copyfile(manifest_file, os.path.join(self.output_dir, 'manifest.json'))

        # Do the Bible inspection HERE
        #        inspector = BibleInspection(self.output_dir)
        #        inspector.run()
        #        for warning in inspector.warnings:
        #            self.warning_message(warning)
        #        for error in inspector.errors:
        #            self.error_message(error)

        #        complete_html = html_template.safe_substitute(content=complete_html)
        #        write_file(os.path.join(self.output_dir, 'all.html'), complete_html)
        #        self.log_message('Made one HTML of all bibles in all.html.')
        #        self.log_message('Finished processing Markdown files.')

        self.logger.info('Finished processing Bible USFM files.')
