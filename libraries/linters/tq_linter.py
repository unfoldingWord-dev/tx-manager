from __future__ import print_function, unicode_literals
import os
from libraries.app.app import App
from libraries.client.preprocessors import TqPreprocessor
from libraries.linters.markdown_linter import MarkdownLinter
from libraries.door43_tools.bible_books import BOOK_NUMBERS


class TqLinter(MarkdownLinter):

    def lint(self):
        """
        Checks for issues with translationQuestions

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return bool:
        """
        for book in BOOK_NUMBERS: 
            found_files = False
            link = self.get_link_for_book('{0}-{1}'.format(BOOK_NUMBERS[book], book.upper()))
            file_path = os.path.join(self.source_dir, link)
            for root, dirs, files in os.walk(file_path):
                if root == file_path:
                    continue  # skip book folder

                for file in files:
                    parts = os.path.splitext(file)
                    if (len(parts) > 1) and (parts[1] == ".md"):
                        found_files = True
                        break

                if found_files:
                    break

            if not found_files:
                msg = "missing book: '{0}'".format(link)
                self.log.warnings.append(msg)
                App.logger.debug(msg)

        return super(TqLinter, self).lint()  # Runs checks on Markdown, using the markdown linter

    def get_link_for_book(self, book):
        parts = book.split('-')
        link = book
        if len(parts) > 1:
            link = parts[1].lower()
        return link
