from __future__ import print_function, unicode_literals
from libraries.checkers.checker import Checker


class UdbChecker(Checker):

    def run(self):
        """
        Checks for issues with the UDB

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.usfm)
        self.converted_dir is the directory of converted files (.html)
        :return:
        """
        super(UdbChecker, self).run()
        pass
