# -*- coding: utf-8 -*-
#

# Script for verifying proper USFM.
# Uses parseUsfm module.
# Place this script in the USFM-Tools folder.

from __future__ import print_function, unicode_literals

# import charset # $ pip install chardet
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

# chapter marker
chapter_marker_re = re.compile(r'\\c', re.UNICODE)

# verse marker
verse_marker_re = re.compile(r'\\v', re.UNICODE)

WHITE_SPACE = [' ', '\u00A0', '\r', '\n', '\t']
SPACE = [' ', '\u00A0']


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
    nMargin = 0
    nQuotes = 0
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
        State.nMargin = 0
        State.nQuotes = 0

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
        State.nParagraphs = 0
        State.nMargin = 0
        State.nQuotes = 0
        State.verse = 0
        State.needVerseText = False
        State.textOkayHere = False
        State.lastRef = State.reference
        State.reference = State.ID + " " + str(State.chapter)

    def addParagraph(self):
        State.nParagraphs += State.nParagraphs + 1
        State.textOkayHere = True

    def addMargin(self):
        State.nMargin += State.nMargin + 1
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
        State.nQuotes += State.nQuotes + 1
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
            report_error(state.reference + " - Should have " + str(state.nVerses(state.ID, state.chapter)) + " verses" + '\n')

def verifyNotEmpty(filename):
    state = State()
    if not state.ID or state.chapter == 0:
        report_error(filename + " - File may be empty.\n")

def verifyIdentification(book_code):
    state = State()
    if not state.ID:
        report_error(book_code + " - Missing \\id tag")
    elif (book_code is not None) and (book_code != state.ID):
        report_error(state.ID + " - Found in \\id tag does not match code '" + book_code + "'' found in file name")

    if not state.IDE:
        report_error(book_code + " - Missing \\ide tag")

    if not state.heading:
        report_error(book_code + " - Missing \\h tag")

    if not state.toc1:
        report_error(book_code + " - Missing \\toc1 tag")

    if not state.toc2:
        report_error(book_code + " - Missing \\toc2 tag")

    if not state.toc3:
        report_error(book_code + " - Missing \\toc3 tag")

    if not state.mt:
        report_error(book_code + " - Missing \\mt tag")

def get_reference(book, chapter, verse=None):
    ref = book + " " + str(chapter)
    if verse is not None:
          ref += ":" + str(verse)
    return ref

def verifyChapterAndVerseMarkers(text, book):
    pos = 0
    last_ch = 1
    for chapter_current in chapter_marker_re.finditer(text):
        start = chapter_current.start()
        end = chapter_current.end()
        char = text[end]
        if (char >= 'a') and (char <= 'z'):
            continue  #  skip non-chapter markers
        has_space = char in SPACE
        if has_space:
            end += 1
        char = text[start - 1]
        nl_before = (char == '\n') or (char == '\r')
        ch_num, has_space_after = get_number(text, end)
        if ch_num >= 0:
            if not has_space:
                add_error(text, book, "Missing space before chapter number: '{0}'", start, last_ch)
            elif not has_space_after:
                add_error(text, book, "Missing new line after chapter marker: '{0}'", start, last_ch)
            elif not nl_before:
                add_error(text, book, "Missing new line before chapter marker: '{0}'", start-4, last_ch)
            check_chapter(text, book, last_ch, pos, start)
            last_ch = ch_num
            pos = end
        else:
            add_error(text, book, "Invalid chapter number: '{0}'", start, last_ch)

    check_chapter(text, book, last_ch, pos, len(text))  # check last chapter

def add_error(text, book, message, pos, chapter, verse=None):
    length = 13
    example = text[pos: pos + length]
    report_error(get_reference(book, chapter, verse) + " - " + message.format(example))

def check_chapter(text, book, chapter_num, start, end):
    last_vs = 1
    for verse_current in verse_marker_re.finditer(text, start, end):
        start = verse_current.start()
        end = verse_current.end()
        char = text[end]
        has_space = char in SPACE
        if has_space:
            end += 1
        char = text[start - 1]
        space_before = char in WHITE_SPACE
        vs_num, has_space_after = get_number(text, end)
        if vs_num >= 0:
            if not has_space:
                add_error(text, book, "Missing space before verse number: '{0}'", start, chapter_num, last_vs)
            elif not has_space_after:
                add_error(text, book, "Missing space after verse number: '{0}'", start, chapter_num, last_vs)
            elif not space_before:
                add_error(text, book, "Missing space before verse marker: '{0}'", start-4, chapter_num, last_vs)
            last_vs = vs_num
        else:
            add_error(text, book, "Invalid verse number: '{0}'", start, chapter_num, last_vs)

def get_number(text, start):
    digits = ''
    has_white_space = False
    for pos in range(start, len(text)):
        c = text[pos]
        if (c >= '0') and (c <= '9'):
            digits += c
            continue
        has_white_space = (c in WHITE_SPACE)
        break
    if len(digits) > 0:
        return int(digits), has_white_space
    return -1, has_white_space

def verifyChapterCount():
    state = State()
    if state.ID:
        expected_chapters = state.nChapters(state.ID)
        if len(state.chapters) != expected_chapters:
            for i in range(1, expected_chapters + 1):
                if i not in state.chapters:
                    report_error(state.ID + " " + str(i) + " - Missing chapter " + "\n")

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
    if state.lang_code and (state.lang_code[0:2] != 'en'):  # no need to translate english
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
        report_error(state.reference + " - Invalid ID: " + id + '\n')
        return
    if code in state.getIDs():
        report_error(state.reference + " - Duplicate ID: " + id + '\n')
        return
    state.loadVerseCounts()
    for k in State.verseCounts:  # look for match in bible names
        if k == code:
            state.addID(code)
            return
    report_error(state.reference + " - Invalid Code '" + code + "' in ID: '" + id + "'\n")

def takeC(c):
    state = State()
    state.addChapter(c)
    if len(state.IDs) == 0:
        report_error(state.reference + " - Missing ID before chapter: " + c + '\n')
    if state.chapter < state.lastChapter:
        report_error(state.reference + " - Chapter out of order" + '\n')
    elif state.chapter == state.lastChapter:
        report_error(state.reference + " - Duplicate chapter" + '\n')
    elif state.chapter > state.lastChapter + 2:
        report_error(state.lastRef + " - Missing chapters between this and: " + state.reference + '\n')
    elif state.chapter > state.lastChapter + 1:
        report_error(state.lastRef + " - Missing chapter between this and: " + state.reference + '\n')

def takeP():
    state = State()
    state.addParagraph()

def takeM():
    state = State()
    state.addMargin()

def takeV(v):
    state = State()
    state.addVerses(v)
    if state.lastVerse == 0:  # if first verse in chapter
        if len(state.IDs) == 0 and state.chapter == 0:
            report_error(state.reference + " " + v + " - Missing ID before verse" + '\n')
        if state.chapter == 0:
            report_error(state.reference + " - Missing chapter tag" + '\n')
        if (state.nParagraphs == 0) and (state.nQuotes == 0) and (state.nMargin == 0):
            report_error(state.reference + " - Missing paragraph marker (\\p), margin (\\m) or quote (\\q) before: "
                         + '\n')

    if state.verse < state.lastVerse and state.addError(state.lastRef):
        report_error(state.reference + " - Verse out of order: after " + state.lastRef + '\n')
        state.addError(state.reference)
    elif state.verse == state.lastVerse:
        report_error(state.reference + " - Duplicated verse" + '\n')
    elif state.verse > state.lastVerse + 1 and state.addError(state.lastRef):
        if state.lastRef == 'MAT 17:20' and state.reference == 'MAT 17:22':
            exception = 'MAT 17:21'
        elif state.lastRef == 'MAT 18:10' and state.reference == 'MAT 18:12':
            exception = 'MAT 18:11'
        else:
            report_error(state.lastRef + " - Missing verse(s) between this and: " + state.reference + '\n')

def takeText(t):
    state = State()
    global lastToken
    if not state.textOkay() and not lastToken.isM() and not lastToken.isFS() and not lastToken.isFE()\
            and not lastToken.isSP() and not lastToken.isD():
        if t[0] == '\\':
            report_error(state.reference + " - Nearby uncommon or invalid marker" + '\n')
        else:
            # print "Missing verse marker before text: <" + t.encode('utf-8') + "> around " + state.reference
            # report_error("Missing verse marker or extra text around " + state.reference + ": <" + t[0:10] + '>.\n')
            report_error(state.reference + " - Missing verse marker or extra text nearby " + '\n')
        if lastToken:
            report_error(state.reference + " - Preceding Token.type was " + lastToken.getType() + '\n')
        else:
            report_error(state.reference + " - No preceding Token\n")
    state.addText()

def takeUnknown(state, token):
    value = token.getValue()
    report_error( state.reference + " - Unknown Token: '\\" + value + '\n')

# Returns True if token is the start of a footnote - note that verse can contain footnote for more reasons than just
#       does not appear in some manuscripts.
def isFootnoted(token):
    state = State()
    footnoted = token.isFS()
    # and state.reference in { 'MAT 17:21', 'MAT 18:11', 'MAT 23:14', 'MRK 7:16', 'MRK 9:44', 'MRK 9:46', 'MRK 11:26', 'MRK 15:28', 'MRK 16:9', 'MRK 16:12', 'MRK 16:14', 'MRK 16:17', 'MRK 16:19', 'LUK 17:36', 'LUK 23:17', 'JHN 5:4', 'JHN 7:53', 'JHN 8:1', 'JHN 8:4', 'JHN 8:7', 'JHN 8:9', 'ACT 8:37', 'ACT 15:34', 'ACT 24:7', 'ACT 28:29', 'ROM 16:24' }
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
        report_error(state.reference + " - Empty verse" + '\n')
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
    elif token.isP() or token.isPI() or token.isNB():
        takeP()
    elif token.isV():
        takeV(token.value)
    elif token.isTEXT():
        takeText(token.value)
    elif token.isQ() or token.isQ1() or token.isQ2() or token.isQ3():
        state.addQuote()
    elif token.isM() or token.isMI():
        state.addMargin()
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
#     verifyChapterAndVerseMarkers(str, filename)
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
    verifyChapterAndVerseMarkers(unicodestring, book_code)
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