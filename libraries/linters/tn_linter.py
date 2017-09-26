from __future__ import print_function, unicode_literals
from libraries.linters.markdown_linter import MarkdownLinter

from libraries.linters.snippet_comparison import snippet_comparison
from libraries.door43_tools import bible_books
from libraries.general_tools import url_utils

import re

'''
   tn_linter.py
'''
#import httplib2



class TnLinter(MarkdownLinter):

    def lint(self):
        """
        Checks for issues with translationNotes
        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return boolean:
        """
        self.DCSwebaddressmap = {
            'en_tn'  : 'https://git.door43.org/Door43/en_tn/raw/master/',
            'en_ulb' : 'https://git.door43.org/Door43/en_ulb/raw/master/',
            'en_ugl' : 'https://git.door43.org/Door43/en_ugl/raw/master/'
        }

        return super(TnLinter, self).lint()  # Runs checks on Markdown, using the markdown linter

        def getFill(bk):
            if 'psa' in bk.lower():
                return 3
            return 2

    def getulb(self):
        lowerbook = self.book.lower()
        upperbook = self.book.upper()
        ulbDCS = "https://git.door43.org/Door43/en_ulb/raw/master/"
        ulbsrc = ulbDCS + bible_books.BOOK_NUMBERS[lowerbook] + '-' + upperbook + '.usfm' 
        content = url_utils.get_url(ulbsrc) # self.httplib2_instance.request(ulbsrc)
        content = re.sub(r'\n','~',content)
        ulbbook = content
        ulbchapters = re.split(r'\\c\s+',ulbbook)
        thischapter = ulbchapters[int(chapter)]
        ulbchunks = re.split(r'\\s5',thischapter)
        versenum = 1
        usechunk = False
        savechunk = ''
        for ulbchunk in ulbchunks:
            lines = ulbchunk.split('~')
            for line in lines:
                versefound = re.search(r'\\v\s+(\d+)\s+(.+)',line)
                if versefound:
                    versenum = int(versefound.group(1))
                    if versenum >= int(chunk):
                        usechunk = True
                if usechunk:
                    savechunk = savechunk + line + " "
            if usechunk:
                savechunk = savechunk.replace('  ',' ')
                return savechunk
        return ''

    def removepunct (instr) :
        ans = instr
        ans = re.sub(r'[!"\#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]','',ans)
        return ans

    def linter(self):

# REMOVE comment below for DCS integration, and delete following line
#        compare_url = self.compare_url
        compare_url = "https://git.door43.org/Door43/en_tn/compare/b0459647bf6e0998b61d3095f183a7bc636678b8...52739c834a38525a86e5da7990eea7265cb76052"

        all_compared = True
        
        findmodule = re.compile(r'<a\s+class\=\"file\"\s+href\=(.+?)\>(\w{3}\/\d{2,3}\/\d{2,3}\.md)')
        tncontent = url_utils.get_url(compare_url) #  self.httplib2_instance.request(compare_url)
        elements = []
        for i, m in enumerate(findmodule.finditer(tncontent)):
            elements.append(m.group(2))
        for onefile in elements:
            onefile = onefile.replace(".md","")
            fnpieces = onefile.split("/")
            book = fnpieces[0]
            chap = fnpieces[1]
            chnk = fnpieces[2]
            this_compare = snippet_comparison(book,chap,chnk)
            all_compared = all_compared and this_compare

