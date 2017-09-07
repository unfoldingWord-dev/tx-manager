from __future__ import print_function, unicode_literals
from libraries.linters.markdown_linter import MarkdownLinter


class TnLinter(MarkdownLinter):

    def lint(self):
        """
        Checks for issues with translationNotes

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return boolean:
        """
        return super(TnLinter, self).lint()  # Runs checks on Markdown, using the markdown linter
