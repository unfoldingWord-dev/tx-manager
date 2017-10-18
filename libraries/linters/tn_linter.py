from __future__ import print_function, unicode_literals
import os
import re
import urlparse
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
        source_dirs = []
        if not self.convert_only:
            source_dirs = [self.source_dir]
        else:
            for d in self.convert_only:
                source_dirs.append(os.path.join(self.source_dir, d))

        for source in source_dirs:
            for root, dirs, files in os.walk(source):
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
                if link == "toc":
                    continue  # not checking for toc, that will be generated
                if self.convert_only and (link not in self.convert_only):
                    continue
                file_path = os.path.join(self.source_dir, link)
                for root, dirs, files in os.walk(file_path):
                    if root == file_path:
                        continue  # skip book folder

                    if len(files) > 0:
                        found_files = True
                        break

                if not found_files:
                    msg = "missing book: '{0}'".format(link)
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
        link = book
        if len(parts) > 1:
            link = parts[1].lower()
        return link

    def check_for_exclusive_convert(self):
        self.convert_only = []
        if self.source_zip_url and len(self.source_zip_url) > 0:
            parsed = urlparse.urlparse(self.source_zip_url)
            params = urlparse.parse_qsl(parsed.query)
            if params and len(params) > 0:
                for i in range(0, len(params)):
                    item = params[i]
                    if item[0] == 'convert_only':
                        for f in item[1].split(','):
                            base_name = f.split('.')[0]
                            parts = base_name.split('-')
                            if len(parts) > 1:
                                base_name = parts[1]
                            self.convert_only.append(base_name.lower())
                        self.source_zip_url = urlparse.urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                                                                  '', '', ''))
                        break
        return self.convert_only
