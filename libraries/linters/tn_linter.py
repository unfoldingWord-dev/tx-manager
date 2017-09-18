from __future__ import print_function, unicode_literals
from libraries.linters.markdown_linter import MarkdownLinter

from libraries.linters.snippet_comparison import snippet_comparison
'''
   tn_linter.py
'''

import re
import httplib2



class TnLinter(MarkdownLinter):

	def lint(self):
		"""
		Checks for issues with translationNotes
		Use self.log.warning("message") to log any issues.
		self.source_dir is the directory of source files (.md)
		:return boolean:
		"""
		self.httplib2_instance = httplib2.Http()
		self.book_directory = {
				"GEN"		: '01',
				"EXO"		: '02',
				"LEV"		: '03',
				"NUM"		: '04',
				"DEU"		: '05',
				"JOS"		: '06',
				"JDG"		: '07',
				"RUT"		: '08',
				"1SA"		: '09',
				"2SA"		: '10',
				"1KI"		: '11',
				"2KI"		: '12',
				"1CH"		: '13',
				"2CH"		: '14',
				"EZR"		: '15',
				"NEH"		: '16',
				"EST"		: '17',
				"JOB"		: '18',
				"PSA"		: '19',
				"PRO"		: '20',
				"ECC"		: '21',
				"SNG"		: '22',
				"ISA"		: '23',
				"JER"		: '24',
				"LAM"		: '25',
				"EZK"		: '26',
				"DAN"		: '27',
				"HOS"		: '28',
				"JOL"		: '29',
				"AMO"		: '30',
				"OBA"		: '31',
				"JON"		: '32',
				"MIC"		: '33',
				"NAM"		: '34',
				"HAB"		: '35',
				"ZEP"		: '36',
				"HAG"		: '37',
				"ZEC"		: '38',
				"MAL"		: '39',
				"MAT"		: '41',
				"MRK"		: '42',
				"LUK"		: '43',
				"JHN"		: '44',
				"ACT"		: '45',
				"ROM"		: '46',
				"1CO"		: '47',
				"2CO"		: '48',
				"GAL"		: '49',
				"EPH"		: '50',
				"PHP"		: '51',
				"COL"		: '52',
				"1TH"		: '53',
				"2TH"		: '54',
				"1TI"		: '55',
				"2TI"		: '56',
				"TIT"		: '57',
				"PHM"		: '58',
				"HEB"		: '59',
				"JAS"		: '60',
				"1PE"		: '61',
				"2PE"		: '62',
				"1JN"		: '63',
				"2JN"		: '64',
				"3JN"		: '65',
				"JUD"		: '66',
				"REV"		: '67'
		}

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
		upperbook = self.book.upper()
		ulbDCS = "https://git.door43.org/Door43/en_ulb/raw/master/"
		ulbsrc = ulbDCS + self.book_directory[upperbook] + '-' + upperbook + '.usfm' 
		resp,content = self.httplib2_instance.request(ulbsrc)
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
#		compare_url = self.compare_url
		compare_url = "https://git.door43.org/Door43/en_tn/compare/b0459647bf6e0998b61d3095f183a7bc636678b8...52739c834a38525a86e5da7990eea7265cb76052"

		all_compared = True
		
		findmodule = re.compile(r'<a\s+class\=\"file\"\s+href\=(.+?)\>(\w{3}\/\d{2,3}\/\d{2,3}\.md)')
		resp,tncontent = self.httplib2_instance.request(compare_url)
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

