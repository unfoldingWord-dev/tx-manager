# -*- coding: utf-8 -*-
#

# Script for verifying proper USFM.
# Uses parseUsfm module.
# Place this script in the USFM-Tools folder.

from __future__ import print_function, unicode_literals

import codecs
import io
# import charset # $ pip install chardet
import json
import os
import re
import sys

# from subprocess import Popen, PIPE, call
from libraries.usfm_tools import parseUsfm, usfm_verses

# # Set Path for files in support/
# rootdiroftools = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(os.path.join(rootdiroftools,'support'))

# Global variables
# lastToken = parseUsfm.UsfmToken(None)
lastToken = None
vv_re = re.compile(r'([0-9]+)-([0-9]+)')
error_log = None

# chapter or verse missing number or space before
missing_num_re = re.compile(r'(\\[cv][^\u00A0 \na-z]+)|(\\[cv][\u00A0 ][^0-9\n]+)', re.UNICODE)

# chapter with missing missing space after number
chapter_missing_space_re = re.compile(r'(\\c[\u00A0 ][0-9]+[\u00A0 ]*[^^0-9\n\u00A0 ])', re.UNICODE)

#  verse with missing missing space after number
verse_missing_space_re = re.compile(r'(\\v[\u00A0 ][0-9]+[^0-9\n -])|(\\v[\u00A0 ](?:[0-9]+[-\u2013\u2014])[0-9]+[^0-9\n ])', re.UNICODE)


class State:
    IDs = []
    ID = ""
    IDE = ""
    toc1 = ""
    toc2 = ""
    toc3 = ""
    mt = ""
    heading = ""
    master_chapter_label = ""
    chapter_label = ""
    chapter = 0
    nParagraphs = 0
    verse = 0
    lastVerse = 0
    needVerseText = False
    textOkayHere = False
    reference = ""
    lastRef = ""
    chapters = set()
    verseCounts = {}
    errorRefs = set()
    englishWords = []
    lang_code = None

    def reset_all(self):
        self.reset_book()
        State.IDs = []
        State.lastRef = ""
        State.reference = ""
        State.errorRefs = set()

    def reset_book(self):
        State.ID = ""
        State.IDE = ""
        State.toc1 = ""
        State.toc2 = ""
        State.toc3 = ""
        State.mt = ""
        State.heading = ""
        State.master_chapter_label = ""
        State.chapter_label = ""
        State.chapter = 0
        State.lastVerse = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.chapters = set()
        State.nParagraphs = 0

    def setLanguageCode(self, code):
        State.lang_code = code

    def addID(self, id):
        self.reset_book()
        State.IDs.append(id)
        State.ID = id
        State.lastRef = State.reference
        State.reference = id

    def getIDs(self):
        return State.IDs

    def addHeading(self, heading):
        State.heading = heading

    def addIDE(self, ide):
        State.IDE = ide

    def addTOC1(self, toc):
        State.toc1 = toc

    def addTOC2(self, toc):
        State.toc2 = toc

    def addTOC3(self, toc):
        State.toc3 = toc

    def addMT(self, mt):
        State.mt = mt

    def addChapterLabel(self, text):
        if State.chapter == 0:
            State.master_chapter_label = text
        else:
            State.chapter_label = text

    def addChapter(self, c):
        State.lastChapter = State.chapter
        State.chapter = int(c)
        State.chapters.add(State.chapter)
        State.lastVerse = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.lastRef = State.reference
        State.reference = State.ID + " " + c

    def addParagraph(self):
        State.nParagraphs += State.nParagraphs + 1
        State.textOkayHere = True

    # supports a span of verses, e.g. 3-4, if needed. Passes the verse(s) on to addVerse()
    def addVerses(self, vv):
        vlist = []
        if vv.find('-') > 0:
            vv_range = vv_re.search(vv)
            vn = int(vv_range.group(1))
            vnEnd = int(vv_range.group(2))
            while vn <= vnEnd:
                vlist.append(vn)
                vn += 1
        else:
            vlist.append(int(vv))

        for vn in vlist:
            self.addVerse(str(vn))

    def addVerse(self, v):
        State.lastVerse = State.verse
        State.verse = int(v)
        State.needVerseText = True
        State.textOkayHere = True
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(State.chapter) + ":" + v

    def textOkay(self):
        return State.textOkayHere

    def needText(self):
        return State.needVerseText

    def addText(self):
        State.needVerseText = False
        State.textOkayHere = True

    def addQuote(self):
        State.textOkayHere = True

    # Adds the specified reference to the set of error references
    # Returns True if reference can be added
    # Returns False if reference was previously added
    def addError(self, ref):
        success = False
        if ref not in State.errorRefs:
            self.errorRefs.add(ref)
            success = True
        return success

    def getEnglishWords(self):
        if len(State.englishWords) == 0:
            for book in usfm_verses.verses:
                book_data = usfm_verses.verses[book]
                english_name = book_data["en_name"].lower()
                english_words = english_name.split(' ')
                for word in english_words:
                    if word and not isNumber(word):
                        State.englishWords.append(word)
            State.englishWords.sort()
        return State.englishWords

    def loadVerseCounts(self):
        if len(State.verseCounts) == 0:
            State.verseCounts = usfm_verses.verses

            # jsonPath = 'verses.json'
            # if not os.access(jsonPath, os.F_OK):
            #     jsonPath = os.path.dirname(os.path.abspath(__file__)) + "\\" + jsonPath
            # if os.access(jsonPath, os.F_OK):
            #     f = open(jsonPath, 'r')
            #     State.verseCounts = json.load(f)
            #     f.close()
            # else:
            #     report_error("File not found: verses.json\n")

    # Returns the number of chapters that the specified book should contain
    def nChapters(self, id):
        n = 0
        self.loadVerseCounts()
        n = State.verseCounts[id]['chapters']
        return n

        # Returns the number of verses that the specified chapter should contain
    def nVerses(self, id, chap):
        n = 0
        self.loadVerseCounts()
        chaps = State.verseCounts[id]['verses']
        n = chaps[chap-1]
        return n

def report_error(msg):
    if error_log is None:  # if error logging is enabled then don't print
        sys.stderr.write(msg)
    else:
        error_log.append(msg.rstrip(' \t\n\r'))

def verifyVerseCount():
    state = State()
    if not state.ID:
        return -1

    if state.chapter > 0 and state.verse != state.nVerses(state.ID, state.chapter):
        if state.reference != 'REV 12:18':  # Revelation 12 may have 17 or 18 verses
            report_error("Chapter should have " + str(state.nVerses(state.ID, state.chapter)) + " verses: " + state.reference + '\n')

def verifyNotEmpty(filename):
    state = State()
    if not state.ID or state.chapter == 0:
        report_error(filename + " -- may be empty.\n")

def verifyIdentification(book_code):
    state = State()
    if not state.ID:
        report_error("missing \\id tag")
    elif (book_code is not None) and (book_code != state.ID):
        report_error("book code '" + state.ID + "' found in \\id tag does not match code '" + book_code + "' found in file name")

    if not state.IDE:
        report_error("missing \\ide tag")

    if not state.heading:
        report_error("missing \\h tag")

    if not state.toc1:
        report_error("missing \\toc1 tag")

    if not state.toc2:
        report_error("missing \\toc2 tag")

    if not state.toc3:
        report_error("missing \\toc3 tag")

    if not state.mt:
        report_error("missing \\mt tag")

def verifyChapterAndVerseMarkers(text):
    # check for chapter or verse tags without numbers
    for no_num in missing_num_re.finditer(text):
        report_error('Chapter or verse tag invalid: "{0}"'.format(getNotEmptyGroup(no_num)))

    # check for chapter tags missing space after number
    for space in chapter_missing_space_re.finditer(text):
        report_error('Chapter tag invalid: "{0}"'.format(getNotEmptyGroup(space)))

    # check for verse tags missing space after number
    for space in verse_missing_space_re.finditer(text):
        report_error('Verse tag invalid: "{0}"'.format(getNotEmptyGroup(space)))

def getNotEmptyGroup(match):
    for i in range(1, len(match.groups()) + 1):
        value = match.group(i)
        if value is not None:
            return value
    return None

def verifyChapterCount():
    state = State()
    if state.ID:
        expected_chapters = state.nChapters(state.ID)
        if len(state.chapters) != expected_chapters:
            for i in range(1, expected_chapters + 1):
                if i not in state.chapters:
                    report_error(state.ID + " missing chapter " + str(i) + "\n")

# def printToken(token):
#     if token.isV():
#         print("Verse number " + token.value)
#     elif token.isC():
#         print("Chapter " + token.value)
#     elif token.isP():
#         print("Paragraph " + token.value)
#     elif token.isTEXT():
#         print("Text: <" + token.value + ">")
#     else:
#         print(token)

def verifyTextTranslated(text, token):
    found, word = needsTranslation(text)
    if found:
        report_error("Token '\\{0}' has untranslated word '{1}'".format(token, word))

def needsTranslation(text):
    state = State()
    if not state.lang_code or (state.lang_code[0:2] == 'en'):  # no need to translate english
        return False
    english = state.getEnglishWords()
    words = text.split(' ')
    for word in words:
        if word:
            found = binarySearch(english, word.lower())
            if found:
                return True, word
    return False, None

def binarySearch(alist, item):
    first = 0
    last = len(alist)-1
    found = False

    while first <= last and not found:
        midpoint = (first + last)//2
        mid_value = alist[midpoint]
        if mid_value == item:
            found = True
        else:
            if item < mid_value:
                last = midpoint-1
            else:
                first = midpoint+1

    return found

def isNumber(s):
    if s:
        char = s[0]
        if (char >= '0') and (char <= '9'):
            return True
    return False

def takeCL(text):
    state = State()
    state.addChapterLabel(text)
    verifyTextTranslated(text, 'cl')

def takeTOC1(text):
    state = State()
    state.addTOC1(text)
    verifyTextTranslated(text, 'toc1')

def takeTOC2(text):
    state = State()
    state.addTOC2(text)
    verifyTextTranslated(text, 'toc2')

def takeTOC3(text):
    state = State()
    state.addTOC3(text)
    verifyTextTranslated(text, 'toc3')

def takeMT(text):
    state = State()
    state.addMT(text)
    verifyTextTranslated(text, 'mt')

def takeH(heading):
    state = State()
    state.addHeading(heading)
    verifyTextTranslated(heading, 'h')

def takeIDE(ide):
    state = State()
    state.addIDE(ide)

def takeID(id):
    state = State()
    code = '' if not id else id.split(' ')[0]
    if len(code) < 3:
        report_error("Invalid ID: " + id + '\n')
        return
    if code in state.getIDs():
        report_error("Duplicate ID: " + id + '\n')
        return
    state.loadVerseCounts()
    for k in State.verseCounts:  # look for match in bible names
        if k == code:
            state.addID(code)
            return
    report_error("Invalid Code '" + code + "' in ID: '" + id + "'\n")

def takeC(c):
    state = State()
    state.addChapter(c)
    if len(state.IDs) == 0:
        report_error("Missing ID before chapter: " + c + '\n')
    if state.chapter < state.lastChapter:
        report_error("Chapter out of order: " + state.reference + '\n')
    elif state.chapter == state.lastChapter:
        report_error("Duplicate chapter: " + state.reference + '\n')
    elif state.chapter > state.lastChapter + 2:
        report_error("Missing chapters between: " + state.lastRef + " and " + state.reference + '\n')
    elif state.chapter > state.lastChapter + 1:
        report_error("Missing chapter between " + state.lastRef + " and " + state.reference + '\n')

def takeP():
    state = State()
    state.addParagraph()

def takeV(v):
    state = State()
    state.addVerses(v)
    if state.lastVerse == 0:  # if first verse in chapter
        if len(state.IDs) == 0 and state.chapter == 0:
            report_error("Missing ID before verse: " + v + '\n')
        if state.chapter == 0:
            report_error("Missing chapter tag: " + state.reference + '\n')
        if state.nParagraphs == 0:
            report_error("Missing paragraph marker (\\p) before: " + state.reference + '\n')
        if not state.chapter_label and not state.master_chapter_label:
            report_error("Missing chapter label (\\cl) before : " + state.reference + '\n')

    if state.verse < state.lastVerse and state.addError(state.lastRef):
        report_error("Verse out of order: " + state.reference + " after " + state.lastRef + '\n')
        state.addError(state.reference)
    elif state.verse == state.lastVerse:
        report_error("Duplicated verse: " + state.reference + '\n')
    elif state.verse > state.lastVerse + 1 and state.addError(state.lastRef):
        if state.lastRef == 'MAT 17:20' and state.reference == 'MAT 17:22':
            exception = 'MAT 17:21'
        elif state.lastRef == 'MAT 18:10' and state.reference == 'MAT 18:12':
            exception = 'MAT 18:11'
        else:
            report_error("Missing verse(s) between: " + state.lastRef + " and " + state.reference + '\n')

def takeText(t):
    state = State()
    global lastToken
    if not state.textOkay() and not lastToken.isM() and not lastToken.isFS() and not lastToken.isFE():
        if t[0] == '\\':
            report_error("Uncommon or invalid marker around " + state.reference + '\n')
        else:
            # print "Missing verse marker before text: <" + t.encode('utf-8') + "> around " + state.reference
            # report_error("Missing verse marker or extra text around " + state.reference + ": <" + t[0:10] + '>.\n')
            report_error("Missing verse marker or extra text around " + state.reference + '\n')
        if lastToken:
            report_error("  preceding Token.type was " + lastToken.getType() + '\n')
        else:
            report_error("  no preceding Token\n")
    state.addText()

def takeUnknown(state, token):
    value = token.getValue()
    report_error("Unknown Token: '\\" + value + "' at " + state.reference + '\n')

# Returns True if token is the start of a footnote for a verse that does not appear in some manuscripts.
def isFootnoted(token):
    state = State()
    footnoted = token.isFS() and state.reference in { 'MAT 17:21', 'MAT 18:11', 'MAT 23:14', 'MRK 7:16', 'MRK 9:44', 'MRK 9:46', 'MRK 11:26', 'MRK 15:28', 'MRK 16:9', 'MRK 16:12', 'MRK 16:14', 'MRK 16:17', 'MRK 16:19', 'LUK 17:36', 'LUK 23:17', 'JHN 5:4', 'JHN 7:53', 'JHN 8:1', 'JHN 8:4', 'JHN 8:7', 'JHN 8:9', 'ACT 8:37', 'ACT 15:34', 'ACT 24:7', 'ACT 28:29', 'ROM 16:24' }
    if footnoted:
        state.addText()     # footnote counts as text for our purposes
    return footnoted

def isCrossRef(token):
    state = State()
    xref = token.isXS()
    if xref:
        state.addText()     # cross reference counts as text for our purposes
    return xref

def take(token):
    state = State()
    if state.needText() and not token.isTEXT() and not isFootnoted(token) and not isCrossRef(token):
        report_error("Empty verse: " + state.reference + '\n')
    if token.isID():
        takeID(token.value)
    elif token.isIDE():
        takeIDE(token.value)
    elif token.isH():
        takeH(token.value)
    elif token.isTOC1():
        takeTOC1(token.value)
    elif token.isTOC2():
        takeTOC2(token.value)
    elif token.isTOC3():
        takeTOC3(token.value)
    elif token.isMT():
        takeMT(token.value)
    elif token.isCL():
        takeCL(token.value)
    elif token.isC():
        verifyVerseCount()
        takeC(token.value)
    elif token.isP() or token.isPI():
        takeP()
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isQ() or token.isQ1() or token.isQ2() or token.isQ3():
        state.addQuote()
    elif token.isUnknown():
        takeUnknown(state, token)
    global lastToken
    lastToken = token

# def verifyFile(filename):
#     # detect file encoding
#     enc = detect_by_bom(filename, default="utf-8")
#     # print "DECODING: " + enc
#     input = io.open(filename, "tr", 1, encoding=enc)
#     str = input.read(-1)
#     input.close
#
#     print("CHECKING " + filename + ":")
#     sys.stdout.flush()
#     verifyChapterAndVerseMarkers(str)
#     for token in parseUsfm.parseString(str):
#         take(token)
#     verifyNotEmpty(filename)
#     verifyIdentification(None)
#     verifyVerseCount()  # for last chapter
#     verifyChapterCount()
#     state = State()
#     state.addID("")
#     sys.stderr.flush()
#     print("FINISHED CHECKING.\n")

def verify_contents_quiet(unicodestring, filename, book_code, lang_code):
    global error_log
    error_log = []  # enable error logging
    state = State()
    state.reset_all()  # clear out previous values
    state.setLanguageCode(lang_code)
    verifyChapterAndVerseMarkers(unicodestring)
    for token in parseUsfm.parse_string(unicodestring):
        take(token)
    verifyNotEmpty(filename)
    verifyIdentification(book_code)
    verifyVerseCount()  # for last chapter
    verifyChapterCount()
    errors = error_log
    error_log = None  # turn error logging back off
    return errors, state.ID

# def detect_by_bom(path, default):
#     with open(path, 'rb') as f:
#         raw = f.read(4)
#     for enc,boms in \
#             ('utf-8-sig',(codecs.BOM_UTF8)), \
#             ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)), \
#             ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
#         if any(raw.startswith(bom) for bom in boms):
#             return enc
#     return default
#
# def verifyDir(dirpath):
#     for f in os.listdir(dirpath):
#         path = os.path.join(dirpath, f)
#         if os.path.isdir(path):
#             # It's a directory, recurse into it
#             verifyDir(path)
#         elif os.path.isfile(path) and path[-3:].lower() == 'sfm':
#             verifyFile(path)

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         source = raw_input("Enter path to .usfm file or directory containing .usfm files: ")
#     # elif sys.argv[1] == 'hard-coded-path':
#     #     source = r'C:\Users\Larry\Documents\GitHub\Bengali\BENGALI-ULB-OT.BCS\STAGE3'
#     else:
#         source = sys.argv[1]
#
#     if os.path.isdir(source):
#         verifyDir(source)
#     elif os.path.isfile(source):
#         verifyFile(source)
#     else:
#         sys.stderr.write("File not found: " + source + '\n')