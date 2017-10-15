from __future__ import print_function, unicode_literals
import os
import re
from libraries.app.app import App
from libraries.client.preprocessors import TnPreprocessor
from libraries.general_tools import file_utils
from libraries.linters.markdown_linter import MarkdownLinter


class TnLinter(MarkdownLinter):

    # match links of form '](link)'
    link_marker_re = re.compile(r'\]\(([^\n()]+)\)', re.UNICODE)

    def lint(self):
        """
        Checks for issues with translationNotes

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return boolean:
        """
        self.source_dir = os.path.abspath(self.source_dir)
        for root, dirs, files in os.walk(self.source_dir):
            for f in files:
                file_path = os.path.join(root, f)
                parts = os.path.splitext(f)
                if parts[1] == '.md':
                    contents = file_utils.read_file(file_path)
                    self.find_invalid_links(root, f, contents)

        for section in TnPreprocessor.sections:
            book = section['book']
            file_path = os.path.join(self.source_dir, '{0}.md'.format(book))
            if os.path.exists(file_path):
                contents = file_utils.read_file(file_path)
                App.logger.debug("Book {0} found, length={1}".format(book, len(contents)))
                continue
            else:
                found_files = False
                link = self.get_link_for_book(book)
                file_path = os.path.join(self.source_dir, link)
                for root, dirs, files in os.walk(file_path):
                    if root == file_path:
                        continue  # skip book folder

                    if len(files) > 0:
                        found_files = True
                        break

                if not found_files:
                    msg = "missing book: {0}".format(book)
                    self.log.warnings.append(msg)
                    App.logger.debug(msg)

        return super(TnLinter, self).lint()  # Runs checks on Markdown, using the markdown linter

    def find_invalid_links(self, folder, f, contents):
        for link_match in TnLinter.link_marker_re.finditer(contents):
            link = link_match.group(1)
            if link:
                if link[:4] == 'http':
                    continue
                if link.find('.md') < 0:
                    continue

                file_path = os.path.join(folder, link)
                file_path_abs = os.path.abspath(file_path)
                exists = os.path.exists(file_path_abs)
                if not exists:
                    a = self.get_file_link(f, folder)
                    msg = "{0}: contains invalid link: ({1})".format(a, link)
                    self.log.warnings.append(msg)
                    App.logger.debug(msg)

    def get_file_link(self, f, folder):
        parts = folder.split(self.source_dir)
        sub_path = self.source_dir  # default
        if len(parts) == 2:
            sub_path = parts[1][1:]
        url = "https://git.door43.org/{0}/{1}/src/master/{2}/{3}".format(self.repo_owner, self.repo_name,
                                                                         sub_path, f)
        a = '<a href="{0}">{1}/{2}</a>'.format(url, sub_path, f)
        return a

    def get_link_for_book(self, book):
        parts = book.split('-')
        if len(parts) > 1:
            link = parts[1].lower()
        return link
