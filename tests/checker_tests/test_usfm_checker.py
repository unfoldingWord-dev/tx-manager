from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.checkers.usfm_checker import UsfmChecker
from libraries.general_tools.file_utils import unzip, write_file, read_file


class TestUsfmChecker(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    converter_resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../converter_tests/resources')

    def setUp(self):
        """Runs before each test."""
        self.preconvert_dir = os.path.join(self.resources_dir, 'some-bible-dir')  # Change when we have something to test
        self.temp_dir = tempfile.mkdtemp(prefix='temp_bible_')
        self.converted_dir = os.path.join(self.temp_dir, 'bible')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_PhpValid(self):
        out_dir = self.unzip_resource('51-PHP.zip')

        expected_warnings = 0
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpInvalidUsfmFileName(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        os.rename(os.path.join(out_dir, '51-PHP.usfm'), os.path.join(out_dir, '51-PHs.usfm'))

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingUsfmFileName(self):
        out_dir = self.unzip_resource('51-PHP.zip')

        os.rename(os.path.join(out_dir, '51-PHP.usfm'), os.path.join(out_dir, '51-PHP.txt'))

        expected_warnings = 0
        expected_errors = 1
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpDuplicateUsfmFileName(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        shutil.copy(os.path.join(out_dir, '51-PHP.usfm'), os.path.join(out_dir, 'PHP.usfm'))

        expected_warnings = True
        expected_errors = True
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def test_PhpMissingID(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'id', '')

        expected_warnings = True
        expected_errors = False
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def test_PhpIdInvalidCode(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'ide', '\id PH Unlocked Literal Bible')

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingHeading(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'h', '')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingToc1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'toc1', '')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingToc2(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'toc2', '')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingToc3(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'toc3', '')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingMasterClNoError(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'cl', '')  # remove master

        expected_warnings = 0
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingMasterAndChapterClError(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'cl', '')  # remove master label
        self.replace_tag(out_dir, '51-PHP.usfm', 'cl', '')  # remove chapter label

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingMt(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'mt', '')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpUntranslatedHeading(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'h', '\\h Genesis')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpUntranslatedToc1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'toc1', '\\toc1 Genesis')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpUntranslatedToc2(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'toc2', '\\toc2 Genesis')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpUntranslatedToc3(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'toc3', '\\toc3 Genesis')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpUntranslatedCl(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'cl', '\\cl Genesis')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpUntranslatedMt(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', 'mt', '\\mt Genesis')

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingV1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=1, start_vs=1, end_vs=2, replace='')  # remove v1

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpNoSpaceV1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=1, start_vs=1, end_vs=2, replace='\\v1 ')  # replace v1

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpNoSpace2V1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=1, start_vs=1, end_vs=2, replace='\\v 1b ')  # replace v1

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpInvalidV1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=1, start_vs=1, end_vs=2, replace='\\v b ')  # replace v1

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpEmptyV1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=1, start_vs=1, end_vs=2, replace='\\v 1 ')  # replace v1

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpEmptyV1V4(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=3, start_vs=1, end_vs=5, replace='\\v 1-4 ')  # replace v1-4

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpEmptyV1V4NoSpace(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=3, start_vs=1, end_vs=5, replace='\\v1-4 ')  # replace v1-4

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpEmptyV1V4NoSpaceAfter(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=3, start_vs=1, end_vs=5, replace='\\v 1-4b ')  # replace v1-4

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpDuplicateV1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=1, start_vs=1, end_vs=2, replace='\\v 1 stuff \\v 1 more stuff ')  # replace v1

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpV2beforeV1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=1, start_vs=2, end_vs=4, replace='\\v 3 stuff \\v 2 more stuff ')  # replace v2-3

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingLastVerse(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=4, start_vs=23, end_vs=24, replace='')  # remove last verse

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingAfterC2V28(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_verse(out_dir, '51-PHP.usfm', chapter=2, start_vs=28, end_vs=40, replace='')  # remove last verse

        expected_warnings = 3
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingC1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_chapter(out_dir, '51-PHP.usfm', start_ch=1, end_ch=2, replace='')  # remove c1

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpEmptyC1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_chapter(out_dir, '51-PHP.usfm', start_ch=1, end_ch=2, replace='\\c 01\n')  # replace c1

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingC4(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_chapter(out_dir, '51-PHP.usfm', start_ch=4, end_ch=5, replace='')  # remove c4

        expected_warnings = 1
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpNoSpaceC1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', tag='c 01', replace='\c01\n')  # replace c1

        expected_warnings = 4
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpNoSpaceAfterC1(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', tag='c 01', replace='\c 016b\n')  # replace c1

        expected_warnings = 6
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpInvalidChapterNumber(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', tag='c 01', replace='\c b\n')  # replace c1

        expected_warnings = 6
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpInvalidChapterNumberNoSpace(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_tag(out_dir, '51-PHP.usfm', tag='c 01', replace='\cb\n')  # replace c1

        expected_warnings = 3
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    def test_PhpMissingC3C4(self):
        out_dir = self.unzip_resource('51-PHP.zip')
        self.replace_chapter(out_dir, '51-PHP.usfm', start_ch=3, end_ch=5, replace='')  # remove c3-4

        expected_warnings = 2
        expected_errors = 0
        checker = UsfmChecker(out_dir, self.converted_dir)
        checker.run()
        self.verify_results_counts(expected_errors, expected_warnings, checker)

    #
    # helpers
    #

    def replace_tag(self, out_dir, file_name, tag, replace):
        book_path = os.path.join(out_dir, file_name)
        book_text = read_file(book_path)
        start_marker = '\\{0}'.format(tag)
        end_marker = '\\'
        c_start_pos = book_text.find(start_marker)
        c_end_pos = book_text.find(end_marker, c_start_pos + 1)
        previous_section = book_text[:c_start_pos]
        next_section = book_text[c_end_pos:]
        new_text = previous_section + replace + next_section
        write_file(book_path, new_text)

    def replace_chapter(self, out_dir, file_name, start_ch, end_ch, replace):
        book_path = os.path.join(out_dir, file_name)
        book_text = read_file(book_path)
        start_chapter_marker = '\\c {0:02d}'.format(start_ch)
        end_chapter_marker = '\\c {0:02d}'.format(end_ch)
        c_start_pos = book_text.find(start_chapter_marker)
        c_end_pos = book_text.find(end_chapter_marker)
        previous_section = book_text[:c_start_pos]
        next_section = book_text[c_end_pos:]
        new_text = previous_section + replace + next_section
        write_file(book_path, new_text)

    def replace_verse(self, out_dir, file_name, chapter, start_vs, end_vs, replace):
        book_path = os.path.join(out_dir, file_name)
        book_text = read_file(book_path)
        chapter_marker = '\\c {0:02d}'.format(chapter)
        c_pos = book_text.find(chapter_marker)
        previous_section = book_text[:c_pos]
        next_section = book_text[c_pos:]
        start_pos = next_section.find('\\v {0} '.format(start_vs))
        end_pos = next_section.find('\\v {0} '.format(end_vs))
        end_text = ''
        if end_pos >= 0:
            end_text = next_section[end_pos:]
        start_text = next_section[:start_pos]
        new_text = previous_section + start_text + replace + end_text
        write_file(book_path, new_text)

    def replace_verse_to_end(self, out_dir, file_name, chapter, start_vs, replace):
        book_path = os.path.join(out_dir, file_name)
        book_text = read_file(book_path)
        chapter_marker = '\\c {0:02d}'.format(chapter)
        c_pos = book_text.find(chapter_marker)
        previous_section = book_text[:c_pos]
        next_section = book_text[c_pos:]
        start_pos = next_section.find('\\v {0} '.format(start_vs))
        start_text = next_section[:start_pos]
        new_text = previous_section + start_text + replace
        write_file(book_path, new_text)

    def unzip_resource(self, zip_name):
        zip_file = os.path.join(self.converter_resources_dir, zip_name)
        out_dir = os.path.join(self.temp_dir, 'checker_test')
        unzip(zip_file, out_dir)
        return out_dir

    def verify_results_counts(self, expected_errors, expected_warnings, checker):
        errors = checker.log.logs["error"]
        if len(errors) != expected_errors:
            print("\nErrors:")
            for error in errors:
                print(error)
        warnings = checker.log.logs["warning"]
        if len(warnings) != expected_warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(warning)

        self.assertEqual(len(errors), expected_errors)
        self.assertEqual(len(warnings), expected_warnings)

    def verify_results(self, expected_errors, expected_warnings, checker):
        errors = checker.log.logs["error"]
        have_errors = len(errors) > 0
        if have_errors != expected_errors:
            print("\nErrors:")
            for error in errors:
                print(error)
        warnings = checker.log.logs["warning"]
        have_warnings = len(warnings) > 0
        if have_warnings != expected_warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(warning)

        self.assertEqual(have_errors, expected_errors)
        self.assertEqual(have_warnings, expected_warnings)
