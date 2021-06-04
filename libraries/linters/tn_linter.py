from __future__ import print_function, unicode_literals
import os
import re
from libraries.app.app import App
from libraries.door43_tools.bible_books import BOOK_NUMBERS
from libraries.general_tools import file_utils
from libraries.linters.markdown_linter import MarkdownLinter


class TnLinter(MarkdownLinter):

    # match links of form '](link)'
    link_marker_re = re.compile(r'\]\(([^\n()]+)\)', re.UNICODE)

    def __init__(self, single_file=None, *args, **kwargs):
        super(MarkdownLinter, self).__init__(*args, **kwargs)

        self.single_file = single_file
        App.logger.debug("Convert single '{0}'".format(self.single_file))
        self.single_dir = None
        if self.single_file:
            parts = os.path.splitext(self.single_file)
            self.single_dir = self.get_dir_for_book(parts[0])
            App.logger.debug("Single source dir '{0}'".format(self.single_dir))

    def lint(self):
        """
        Checks for issues with translationNotes

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return boolean:
        """
        self.source_dir = os.path.abspath(self.source_dir)
        source_dir = self.source_dir if not self.single_dir else os.path.join(self.source_dir, self.single_dir)
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                file_path = os.path.join(root, f)
                parts = os.path.splitext(f)
                if parts[1] == '.md':
                    contents = file_utils.read_file(file_path)
                    self.find_invalid_links(root, f, contents)

        for dir in BOOK_NUMBERS:
            found_files = False
            if self.single_dir and (dir != self.single_dir):
                continue
            App.logger.debug("Processing folder {0}".format(dir))
            file_path = os.path.join(self.source_dir, dir)
            for root, dirs, files in os.walk(file_path):
                if root == file_path:
                    continue  # skip book folder

                if len(files) > 0:
                    found_files = True
                    break

            if not found_files:
                msg = "missing book: '{0}'".format(dir)
                self.log.warnings.append(msg)
                App.logger.debug(msg)

        results = super(TnLinter, self).lint()  # Runs checks on Markdown, using the markdown linter
        if not results:
            App.logger.debug("Error running MD linter on {0}".format(self.s3_results_key))
        return results

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

    # TODO: does this need to be changed?
    def get_file_link(self, f, folder):
        parts = folder.split(self.source_dir)
        sub_path = self.source_dir  # default
        if len(parts) == 2:
            sub_path = parts[1][1:]
        url = "https://git.door43.org/{0}/{1}/src/master/{2}/{3}".format(self.repo_owner, self.repo_name,
                                                                         sub_path, f)
        a = '<a href="{0}">{1}/{2}</a>'.format(url, sub_path, f)
        return a
