from __future__ import print_function, unicode_literals
from libraries.checkers.checker import Checker


class BibleChecker(Checker):

    def run(self):
        """
        Checks for issues with all Bibles, such as missing books or chapters

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.usfm)
        self.converted_dir is the directory of converted files (.html)
        :return:
        """
        pass
