from __future__ import print_function, unicode_literals
import os
import re
from libraries.app.app import App
from libraries.general_tools import file_utils
from libraries.linters.markdown_linter import MarkdownLinter


class TwLinter(MarkdownLinter):

    link_marker_re = re.compile(r'\]\(([^\n()]+)\)', re.UNICODE)

    def lint(self):
        """
        Checks for issues with translationWords

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return bool:
        """
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
                    msg = "{0}: contains invalid link: ({1})".format(f, link)
                    self.log.warnings.append(msg)
                    App.logger.debug(msg)
