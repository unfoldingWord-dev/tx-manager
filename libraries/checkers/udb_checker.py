from __future__ import print_function, unicode_literals
from libraries.checkers.usfm_checker import UsfmChecker


class UdbChecker(UsfmChecker):

    def run(self):
        """
        Checks for issues with the UDB

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.usfm)
        self.converted_dir is the directory of converted files (.html)
        :return:
        """
        super(UdbChecker, self).run()  # Runs checks on any Bible, such as missing chapters
        pass
