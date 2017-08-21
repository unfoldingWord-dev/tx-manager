from __future__ import print_function, unicode_literals
import codecs
import os
import traceback
from libraries.checkers.checker import Checker
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.usfm_tools import verifyUSFM, usfm_verses


class UsfmChecker(Checker):

    def __init__(self, preconvert_dir, converted_dir, log=None):
        super(UsfmChecker, self).__init__(preconvert_dir, converted_dir, log=None)

        # TODO blm - these are stubs until ported over to lint handler
        self.found_books = []
        self.commit_data = {}
        self.rc = {}

    def run(self):
        """
        Checks for issues with all Bibles, such as missing books or chapters

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files (.usfm)
        self.converted_dir is the directory of converted files (.html)
        :return:
        """

        lang_code = self.rc.resource.language.identifier
        valid_lang_code = PageMetrics().validate_language_code(lang_code)
        if not valid_lang_code:
            self.log.warning("Invalid language code: " + lang_code)

        for root, dirs, files in os.walk(self.preconvert_dir):
            for f in files:
                if f[-3:].lower() != 'sfm':  # only usfm files
                    continue

                file_path = os.path.join(root, f)
                sub_path = '.' + file_path[len(self.preconvert_dir):]
                self.parse_file(file_path, sub_path, f)

        found_book_count = len(self.found_books)
        if found_book_count == 0:
            self.log.error("No translations found")
        elif found_book_count == 1:
            pass  # this is OK, presume this was a single book project
        else:
            for book in usfm_verses.verses:
                if book not in self.found_books:
                    book_data = usfm_verses.verses[book]
                    self.log.warning("Missing translation for " + book_data["en_name"])

    def parse_file(self, file_path, sub_path, file_name):

        # which bible book is this?
        file_name_parts = file_name.split('.')
        book_full_name = file_name_parts[0].upper()
        book_code = book_full_name
        book_name_parts = book_full_name.split('-')
        if len(book_name_parts) > 1:
            book_code = book_name_parts[1]

        try:
            with codecs.open(file_path, 'r', 'utf-8') as in_file:
                book_text = in_file.read()

            self.parse_usfm_text(sub_path, file_name, book_text, book_full_name, book_code)

        except Exception as e:
            self.log.error("Failed to open book '{0}', exception: {1}".format(file_name, str(e)))

    def parse_usfm_text(self, sub_path, file_name, book_text, book_full_name, book_code):
        try:
            lang_code = self.rc.resource.language.identifier
            errors, found_book_code = verifyUSFM.verify_contents_quiet(book_text, book_full_name, book_code, lang_code)

            if found_book_code:
                book_code = found_book_code

            if book_code:
                if book_code in self.found_books:
                    self.log.error("File '{0}' has same code '{1}' as previous file".format(sub_path, book_code))
                self.found_books.append(book_code)

            if len(errors):
                prefix = "File '{0}' book code '{1}': ".format(sub_path, book_code)
                for error in errors:
                    self.log.warning(prefix + error)

        except Exception as e:
            # for debugging
            print("Failed to verify book '{0}', exception: {1}\n{2}".format(file_name, str(e),
                                                                            traceback.format_exc()))
            self.log.error("Failed to verify book '{0}', exception: {1}".format(file_name, str(e)))
