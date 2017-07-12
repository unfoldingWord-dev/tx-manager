from __future__ import print_function, unicode_literals
from libraries.checkers.bible_checker import BibleChecker


class UlbChecker(BibleChecker):

    def run(self):
        """
        Checks for issues with the ULB

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.usfm)
        self.converted_dir is the directory of converted files (.html)
        This also calls run() on the parent class which is the Bible checker
        :return:
        """
        super(UlbChecker, self).run()  # Runs checks on any Bible, such as missing chapters
        pass
