from __future__ import print_function, unicode_literals
from libraries.linters.markdown_linter import MarkdownLinter


class TqLinter(MarkdownLinter):

    def run(self):
        """
        Checks for issues with translationQuestions

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return:
        """
        super(TqLinter, self).lint()  # Runs checks on Markdown, using the markdown linter
