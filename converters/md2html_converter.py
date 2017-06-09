from __future__ import print_function, unicode_literals
import os
import string
import markdown
import codecs
from shutil import copyfile
from general_tools.file_utils import write_file
from converter import Converter
from door43_tools.obs_handler import OBSInspection
from door43_tools.obs_data import obs_data


class Md2HtmlConverter(Converter):

    def convert(self):
        if self.resource == "obs":
            self.convert_obs()
            return True
        else:
            self.convert_markdown()
            return True

    def convert_obs(self):
        self.log.info('Processing OBS markdown files')

        # find the first directory that has md files.
        files = self.get_files()

        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'obs-template.html')) as template_file:
            html_template = string.Template(template_file.read())

        found_chapters = {}

        for filename in files:
            if filename.endswith('.md'):
                # Convert files that are markdown files
                with codecs.open(filename, 'r', 'utf-8-sig') as md_file:
                    md = md_file.read()
                html = markdown.markdown(md)
                html = html_template.safe_substitute(content=html)
                base_name = os.path.splitext(os.path.basename(filename))[0]
                found_chapters[base_name] = True
                html_filename = base_name + ".html"
                output_file = os.path.join(self.output_dir, html_filename)
                write_file(output_file, html)
                self.log.info('Converted {0} to {1}.'.format(os.path.basename(filename), os.path.basename(html_filename)))

                # Do the OBS inspection (this now operates on a single file instead of folder)
                # QUESTION: Should this be done separately after conversion????
                inspector = OBSInspection(output_file, self.log)
                try:
                    inspector.run()
                except Exception as e:
                    self.log.warning('Chapter {0}: failed to run OBS inspector: {1}'.format(base_name, e.message))
            else:
                # Directly copy over files that are not markdown files
                try:
                    output_file = os.path.join(self.output_dir, os.path.basename(filename))
                    if not os.path.exists(output_file):
                        copyfile(filename, output_file)
                except:
                    pass

        for chapter in sorted(obs_data['chapters']): # verify all expected chapters are present
            found_chapter = found_chapters.get(chapter)
            if not found_chapter:
                self.log.warning('Chapter {0} is missing!'.format(chapter))
        self.log.info('Finished processing OBS Markdown files.')

    def convert_markdown(self):
        self.log.info('Processing Markdown files')

        # find the first directory that has md files.
        files = self.get_files()

        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'template.html')) as template_file:
            html_template = string.Template(template_file.read())

        found_chapters = {}

        for filename in files:
            if filename.endswith('.md'):
                # Convert files that are markdown files
                with codecs.open(filename, 'r', 'utf-8-sig') as md_file:
                    md = md_file.read()
                html = markdown.markdown(md)
                html = html_template.safe_substitute(title=self.resource.upper(), content=html)
                base_name = os.path.splitext(os.path.basename(filename))[0]
                found_chapters[base_name] = True
                html_filename = base_name + ".html"
                output_file = os.path.join(self.output_dir, html_filename)
                write_file(output_file, html)
                self.log.info('Converted {0} to {1}.'.format(os.path.basename(filename), os.path.basename(html_filename)))
            else:
                # Directly copy over files that are not markdown files
                try:
                    output_file = os.path.join(self.output_dir, os.path.basename(filename))
                    if not os.path.exists(output_file):
                        copyfile(filename, output_file)
                except:
                    pass
        self.log.info('Finished processing Markdown files.')
