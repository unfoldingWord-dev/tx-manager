# coding=utf-8
from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
import time
from libraries.general_tools import file_utils
from libraries.linters.usfm_linter import UsfmLinter
from libraries.general_tools.file_utils import write_file, read_file, unzip
from libraries.resource_container.ResourceContainer import RC


class TestUsfmLinter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
    php_repo_path = os.path.join(resources_dir, 'es_php_text_ulb')
    php_file_name = '51-PHP.usfm'
    php_file_path = os.path.join(php_repo_path, php_file_name)

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_usfm_')
        self.rc = RC(directory=self.php_repo_path)

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_PhpValid(self):
        out_dir = self.copy_resource(self.php_file_path)
        expected_warnings = 0
        linter = self.run_linter(out_dir)
        self.verify_results_counts(expected_warnings, linter)

    def test_PhpValidWithFootnoteAndRefsTags(self):
        out_dir = self.copy_resource(self.php_file_path)
        replace = read_file(os.path.join(self.resources_dir, 'footnote_n_refs_example.txt'))
        self.replace_verse(out_dir, self.php_file_name, chapter=2, start_vs=1, end_vs=16, replace=replace)  # replace v1
        expected_warnings = 0
        linter = self.run_linter(out_dir)
        self.verify_results_counts(expected_warnings, linter)

    def test_PhpValidWithFormattingTags(self):
        out_dir = self.copy_resource(self.php_file_path)
        replace = read_file(os.path.join(self.resources_dir, 'formatting_example.txt'))
        self.replace_verse(out_dir, self.php_file_name, chapter=2, start_vs=1, end_vs=13, replace=replace)  # replace v1
        expected_warnings = 0
        linter = self.run_linter(out_dir)
        self.verify_results_counts(expected_warnings, linter)

    def test_PhpInvalidUsfmFileName(self):
        out_dir = self.copy_resource(self.php_file_path)
        os.rename(os.path.join(out_dir, self.php_file_name), os.path.join(out_dir, '51-PHs.usfm'))
        expected_warnings = 1
        linter = self.run_linter(out_dir)
        self.verify_results_counts(expected_warnings, linter)

    def test_PhpMissingUsfmFileName(self):
        out_dir = self.copy_resource(self.php_file_path)
        os.rename(os.path.join(out_dir, self.php_file_name), os.path.join(out_dir, '51-PHP.txt'))
        expected_warnings = 1
        linter = self.run_linter(out_dir)
        self.verify_results_counts(expected_warnings, linter)

    def test_PhpDuplicateUsfmFileName(self):
        out_dir = self.copy_resource(self.php_file_path)
        shutil.copy(os.path.join(out_dir, self.php_file_name), os.path.join(out_dir, 'PHP.usfm'))
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingID(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'id', '')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpEmptyID(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'id', '\id')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingIDAndC1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'id', '')
        self.replace_tag(out_dir, self.php_file_name, 'c 01', '')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpIdInvalidCode(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'id', '\id PH Unlocked Literal Bible')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpInvalidIdLength(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'id', '\id PH')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpDuplicateID(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.append_text(out_dir, self.php_file_name, '\id  PHP Unlocked Literal Bible')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingHeading(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'h', '')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingToc1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'toc1', '')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingToc2(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'toc2', '')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingToc3(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'toc3', '')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingMasterClNoError(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'cl', '')  # remove master
        expected_warnings = 0
        linter = self.run_linter(out_dir)
        self.verify_results_counts(expected_warnings, linter)

    def test_PhpMissingMasterAndChapterClError(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'cl', '')  # remove master label
        self.replace_tag(out_dir, self.php_file_name, 'cl', '')  # remove chapter label
        expected_warnings = False
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingMt(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'mt', '')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpUntranslatedHeading(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'h', '\\h Genesis')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpUntranslatedToc1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'toc1', '\\toc1 Genesis')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpUntranslatedToc2(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'toc2', '\\toc2 Genesis')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpUntranslatedToc3(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'toc3', '\\toc3 Genesis')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpUntranslatedCl(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'cl', '\\cl Genesis')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpUntranslatedMt(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, 'mt', '\\mt Genesis')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingP(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, tag='p', replace='')  # remove p
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingV1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=1, start_vs=1, end_vs=2, replace='')  # remove v1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingV1Tag(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, tag='v 1', replace='first verse stuff\n')  # remove v1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpNoSpaceV1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=1, start_vs=1, end_vs=2, replace='\\v1 ')  # replace v1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpNoSpace2V1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=1, start_vs=1, end_vs=2, replace='\\v 1b ')  # replace v1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpInvalidV1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=1, start_vs=1, end_vs=2, replace='\\v b ')  # replace v1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpEmptyV1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=1, start_vs=1, end_vs=2, replace='\\v 1 ')  # replace v1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpEmptyV1V4(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=3, start_vs=1, end_vs=5, replace='\\v 1-4 ')  # replace v1-4
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpEmptyV1V4NoSpace(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=3, start_vs=1, end_vs=5, replace='\\v1-4 ')  # replace v1-4
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpEmptyV1V4NoSpaceAfter(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=3, start_vs=1, end_vs=5, replace='\\v 1-4b ')  # replace v1-4
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpDuplicateV1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=1, start_vs=1, end_vs=2, replace='\\v 1 stuff \\v 1 more stuff ')  # replace v1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpV2beforeV1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=1, start_vs=2, end_vs=4, replace='\\v 3 stuff \\v 2 more stuff ')  # replace v2-3
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingtoken(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.append_text(out_dir, self.php_file_name, '\n\\\n')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingtokenEof(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.append_text(out_dir, self.php_file_name, '\n\\')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpEscapedtoken(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.append_text(out_dir, self.php_file_name, '\n\\\\\n')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpEscapedtokenEOF(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.append_text(out_dir, self.php_file_name, '\n\\\\')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingLastVerse(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=4, start_vs=23, end_vs=24, replace='')  # remove last verse
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingAfterC2V28(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_verse(out_dir, self.php_file_name, chapter=2, start_vs=28, end_vs=40, replace='')  # remove last verse
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingC1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_chapter(out_dir, self.php_file_name, start_ch=1, end_ch=2, replace='')  # remove c1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpEmptyC1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_chapter(out_dir, self.php_file_name, start_ch=1, end_ch=2, replace='\\c 01\n')  # replace c1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingC4(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_chapter(out_dir, self.php_file_name, start_ch=4, end_ch=5, replace='')  # remove c4
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpExtraC4(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.append_text(out_dir, self.php_file_name, '\n\\c 4\n')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpExtraC2(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.append_text(out_dir, self.php_file_name, '\n\\c 2\n')
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingC1Tag(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, tag='c 01', replace='')  # remove c1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpNoSpaceC1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, tag='c 01', replace='\c01\n')  # replace c1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpNoSpaceAfterC1(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, tag='c 01', replace='\c 016b\n')  # replace c1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpInvalidChapterNumber(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, tag='c 01', replace='\c b\n')  # replace c1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpInvalidChapterNumberNoSpace(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_tag(out_dir, self.php_file_name, tag='c 01', replace='\cb\n')  # replace c1
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingC2C3(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_chapter(out_dir, self.php_file_name, start_ch=2, end_ch=4, replace='')  # remove c2-3
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_PhpMissingC3C4(self):
        out_dir = self.copy_resource(self.php_file_path)
        self.replace_chapter(out_dir, self.php_file_name, start_ch=3, end_ch=5, replace='')  # remove c3-4
        expected_warnings = True
        linter = self.run_linter(out_dir)
        self.verify_results(expected_warnings, linter)

    def test_parse_file_missing_file(self):
        out_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix='linter_test')
        file_path = os.path.join(out_dir, self.php_file_name)  # non-existant file
        sub_path = self.php_file_name
        file_name = "PHP.usfm"
        expected_warnings = 1
        linter = UsfmLinter(source_dir=out_dir, rc=self.rc)
        linter.parse_file(file_path, sub_path, file_name)
        self.verify_results_counts(expected_warnings, linter)

    def test_parse_usfm_text_none(self):
        sub_path = self.php_file_name
        file_name = "51-PHP.usfm"
        book_full_name = "51-PHP"
        book_code = "PHP"
        book_text = None
        expected_warnings = 1
        linter = UsfmLinter(rc=self.rc)
        linter.parse_usfm_text(sub_path, file_name, book_text, book_full_name, book_code)
        self.verify_results_counts(expected_warnings, linter)

    def test_parse_usfm_text_empty(self):
        sub_path = self.php_file_name
        file_name = "51-PHP.usfm"
        book_full_name = "51-PHP"
        book_code = "PHP"
        book_text = ''
        expected_warnings = 1
        linter = UsfmLinter(rc=self.rc)
        linter.parse_usfm_text(sub_path, file_name, book_text, book_full_name, book_code)
        self.verify_results_counts(expected_warnings, linter)

    @unittest.skip("Skip test for time reasons - leave for standalone testing")
    def test_EnUlbValid(self):
        out_dir = self.unzip_resource('en_ulb.zip')
        expected_warnings = 0
        start = time.time()
        rc = RC(out_dir)
        linter = UsfmLinter(source_dir=out_dir, rc=rc)
        linter.run()
        elapsed_seconds = int(time.time() - start)
        print("Checking time was " + str(elapsed_seconds) + " seconds")
        self.verify_results_counts(expected_warnings, linter)

    def test_EnUlbValidSubset(self):
        check_files = ['19-PSA.usfm','22-SNG.usfm','24-JER.usfm','25-LAM.usfm','35-HAB.usfm']
        out_dir = self.unzip_resource_only('en_ulb.zip', check_files)
        expected_warnings = 0
        start = time.time()
        rc = RC(out_dir)
        linter = UsfmLinter(source_dir=out_dir, rc=rc)
        linter.run()
        elapsed_seconds = int(time.time() - start)
        print("Checking time was " + str(elapsed_seconds) + " seconds")
        self.verify_results_counts(expected_warnings, linter)

    def test_EnUlbValidConvertSingle(self):
        out_dir = self.unzip_resource('en_ulb.zip')
        expected_warnings = 0
        start = time.time()
        rc = RC(out_dir)
        convert_only = '51-PHP.usfm'
        linter = UsfmLinter(source_dir=out_dir, rc=rc, single_file=convert_only)
        linter.run()
        elapsed_seconds = int(time.time() - start)
        print("Checking time was " + str(elapsed_seconds) + " seconds")
        self.verify_results_counts(expected_warnings, linter)

    #
    # helpers
    #

    def run_linter(self, out_dir):
        linter = UsfmLinter(source_dir=out_dir, rc=self.rc)
        linter.run()
        return linter

    def unzip_resource_only(self, zip_name, test_only):
        unpack_folder = self.unzip_resource(zip_name)
        out_dir = os.path.join(self.temp_dir, 'test_folder')
        file_utils.make_dir(out_dir)
        for f in test_only:
            shutil.copy(os.path.join(unpack_folder, f), out_dir)
        shutil.rmtree(unpack_folder, ignore_errors=True)
        return out_dir

    def append_text(self, out_dir, file_name, append):
        book_path = os.path.join(out_dir, file_name)
        book_text = read_file(book_path)
        new_text = book_text + append
        write_file(book_path, new_text)

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

    def copy_resource(self, file_path):
        out_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix='linter_test')
        shutil.copy(file_path, out_dir)
        return out_dir

    def unzip_resource(self, zip_name):
        zip_file = os.path.join(self.resources_dir, zip_name)
        out_dir = tempfile.mkdtemp(dir=self.temp_dir, prefix='linter_test')
        unzip(zip_file, out_dir)
        return out_dir

    def verify_results_counts(self, expected_warnings, linter):
        warnings = linter.log.warnings
        if len(warnings) != expected_warnings:
            have_warnings = len(warnings) > 0
            if have_warnings:
                print("\nReported Warnings:")
                for warning in warnings:
                    print(warning)
        self.assertEqual(len(warnings), expected_warnings)

    def verify_results(self, expected_warnings, linter):
        warnings = linter.log.warnings
        have_warnings = len(warnings) > 0
        if have_warnings != expected_warnings:
            if have_warnings:
                print("\nReported Warnings:")
                for warning in warnings:
                    print(warning)
        self.assertEqual(have_warnings, expected_warnings)
