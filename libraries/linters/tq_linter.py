from __future__ import print_function, unicode_literals

import os

from libraries.app.app import App
from libraries.client.preprocessors import TqPreprocessor
from libraries.general_tools import file_utils
from libraries.linters.markdown_linter import MarkdownLinter


class TqLinter(MarkdownLinter):

    def lint(self):
        """
        Checks for issues with translationQuestions

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return bool:
        """
        for section in TqPreprocessor.sections:
            book = section['book']
            file_path = os.path.join(self.source_dir, '{0}.md'.format(book))
            if os.path.exists(file_path):
                contents = file_utils.read_file(file_path)
                App.logger.debug("Book {0} found, length={1}".format(book, len(contents)))
                continue
            else:
                found_files = False
                link = self.get_link_for_book(book)
                file_path = os.path.join(self.source_dir, link)
                for root, dirs, files in os.walk(file_path):
                    if root == file_path:
                        continue  # skip book folder

                    if len(files) > 0:
                        found_files = True
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
