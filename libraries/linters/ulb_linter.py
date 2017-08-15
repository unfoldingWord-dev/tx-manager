from __future__ import print_function, unicode_literals
from libraries.linters.usfm_linter import UsfmLinter


class UlbLinter(UsfmLinter):

    def lint(self):
        """
        Checks for issues with the ULB

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.usfm)
        This calls lint() on the parent class which is the USFM linter
        :return:
        """
        super(UlbLinter, self).lint()  # Runs checks on any Bible, such as missing chapters
