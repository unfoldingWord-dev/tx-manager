from __future__ import print_function, unicode_literals
import os
import re
from libraries.app.app import App
from libraries.general_tools import file_utils
from libraries.linters.markdown_linter import MarkdownLinter


class TwLinter(MarkdownLinter):

    # match links of form '](link)'
    link_marker_re = re.compile(r'\]\(([^\n()]+)\)', re.UNICODE)

    def lint(self):
        """
        Checks for issues with translationWords

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return bool:
        """
        self.source_dir = os.path.abspath(self.source_dir)
        for root, dirs, files in os.walk(self.source_dir):
            for f in files:
                file_path = os.path.join(root, f)
                parts = os.path.splitext(f)
                if parts[1] == '.md':
                    contents = file_utils.read_file(file_path)
                    self.find_invalid_links(root, f, contents)

        return super(TwLinter, self).lint()  # Runs checks on Markdown, using the markdown linter

    def find_invalid_links(self, folder, f, contents):
        for link_match in TwLinter.link_marker_re.finditer(contents):
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

    # TODO: change this
    # probably just as simple as changing git.door43.org -> content.bibletranslationtools.org
    def get_file_link(self, f, folder):
        parts = folder.split(self.source_dir)
        sub_path = self.source_dir  # default
        if len(parts) == 2:
            sub_path = parts[1][1:]
        url = "https://git.door43.org/{0}/{1}/src/master/{2}/{3}".format(self.repo_owner, self.repo_name,
                                                                         sub_path, f)
        a = '<a href="{0}">{1}/{2}</a>'.format(url, sub_path, f)
        return a
