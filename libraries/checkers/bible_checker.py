from __future__ import print_function, unicode_literals
import codecs
import os
from general_tools.print_utils import print_warning
from libraries.checkers.checker import Checker
from libraries.checkers.content import Book


class BibleChecker(Checker):

    def run(self):
        """
        Checks for issues with all Bibles, such as missing books or chapters

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.usfm)
        self.converted_dir is the directory of converted files (.html)
        :return:
        """

        unzipped_dir = self.preconvert_dir
        there_were_errors = False
        for root, dirs, files in os.walk(unzipped_dir):

            # only usfm files
            for f in files:

                if f[-3:].lower() != 'sfm':
                    continue

                # which book is this?
                book_name = f.split('.')
                book = Book.create_book(book_name[0])  # type: Book

                if book:
                    with codecs.open(os.path.join(root, f), 'r', 'utf-8') as in_file:
                        book_text = in_file.read()

                    book.set_usfm(book_text)
                    book.clean_usfm()

                    # do basic checks
                    book.verify_usfm_tags()
                    book.verify_chapters_and_verses()
                    if len(book.validation_errors) > 0:
                        there_were_errors = True

        if there_were_errors:
            print_warning('There are source errors.')
            return
