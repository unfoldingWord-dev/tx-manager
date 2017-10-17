from __future__ import print_function, unicode_literals
import os
import string
import markdown
import markdown2
import codecs
from shutil import copyfile
from bs4 import BeautifulSoup
from libraries.general_tools.file_utils import write_file, get_files
from converter import Converter


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
        files = get_files(directory=self.files_dir, exclude=self.EXCLUDED_FILES)

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
                html = html_template.safe_substitute(title=self.source.upper(), content=html)
                base_name = os.path.splitext(os.path.basename(filename))[0]
                found_chapters[base_name] = True
                html_filename = base_name + ".html"
                output_file = os.path.join(self.output_dir, html_filename)
                write_file(output_file, html)
                self.log.info('Converted {0} to {1}.'.format(os.path.basename(filename),
                                                             os.path.basename(html_filename)))
            else:
                # Directly copy over files that are not markdown files
                try:
                    output_file = os.path.join(self.output_dir, os.path.basename(filename))
                    if not os.path.exists(output_file):
                        copyfile(filename, output_file)
                except:
                    pass
        self.log.info('Finished processing OBS Markdown files.')

    def convert_markdown(self):
        self.log.info('Processing Markdown files')

        # find the first directory that has md files.
        files = get_files(directory=self.files_dir, exclude=self.EXCLUDED_FILES)

        current_dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(current_dir, 'templates', 'template.html')) as template_file:
            html_template = string.Template(template_file.read())

        found_chapters = {}

        for filename in files:
            if filename.endswith('.md'):
                # Convert files that are markdown files
                with codecs.open(filename, 'r', 'utf-8-sig') as md_file:
                    md = md_file.read()
                if self.resource == 'ta':
                    html = markdown2.markdown(md, extras=['markdown-in-html', 'tables'])
                else:
                    html = markdown.markdown(md)
                html = html_template.safe_substitute(title=self.resource.upper(), content=html)

                # Change headers like <h1><a id="verbs"/>Verbs</h1> to <h1 id="verbs">Verbs</h1>
                soup = BeautifulSoup(html, 'html.parser')
                for tag in soup.findAll('a', {'id': True}):
                    if tag.parent and tag.parent.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        tag.parent['id'] = tag['id']
                        tag.parent['class'] = tag.parent.get('class', []) + ['section-header']
                        tag.extract()
                html = unicode(soup)

                base_name = os.path.splitext(os.path.basename(filename))[0]
                found_chapters[base_name] = True
                html_filename = base_name + ".html"
                output_file = os.path.join(self.output_dir, html_filename)
                write_file(output_file, html)
                self.log.info('Converted {0} to {1}.'.format(os.path.basename(filename),
                                                             os.path.basename(html_filename)))
            else:
                # Directly copy over files that are not markdown files
                try:
                    output_file = os.path.join(self.output_dir, os.path.basename(filename))
                    if not os.path.exists(output_file):
                        copyfile(filename, output_file)
                except:
                    pass
        self.log.info('Finished processing Markdown files.')
