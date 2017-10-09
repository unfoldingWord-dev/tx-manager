from __future__ import print_function, unicode_literals
import os
from libraries.app.app import App
from libraries.general_tools import file_utils
from libraries.linters.markdown_linter import MarkdownLinter


class TwLinter(MarkdownLinter):

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
                parts = os.path.splitext(file_path)
                if parts[1] == '.md':
                    App.logger.debug("Processing: " + f)
                    contents = file_utils.read_file(file_path)

                    # find uncoverted links
                    self.find_unconverted_link(f, contents, '(../')
                    self.find_unconverted_link(f, contents, '(./')

        return super(TwLinter, self).lint()  # Runs checks on Markdown, using the markdown linter

    def find_unconverted_link(self, f, contents, link):
        pos = contents.find(link)
        while pos >= 0:
            link_start = contents.rfind('[', 0, pos)
            if link_start < 0:
                link_start = 0
            line_start = contents.rfind('\n', 0, pos)
            if line_start > link_start:
                link_start = line_start + 1
            end = contents.find(')', pos + 1)
            invalid_link = contents[link_start:end + 1]
            self.log.warning("{0} - Invalid link: {1}".format(f, invalid_link))
            pos = contents.find(link, end)
