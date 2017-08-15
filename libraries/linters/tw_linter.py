from __future__ import print_function, unicode_literals
from libraries.linters.markdown_linter import MarkdownLinter


class TwLinter(MarkdownLinter):

    def lint(self):
        """
        Checks for issues with translationWords

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return:
        """
        super(TwLinter, self).lint()  # Runs checks on Markdown, using the markdown linter
