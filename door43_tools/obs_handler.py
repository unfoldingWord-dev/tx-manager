from __future__ import print_function, unicode_literals
import os
from bs4 import BeautifulSoup
from converters.convert_logger import ConvertLogger
from obs_data import obs_data


class OBSInspection(object):
    def __init__(self, filename, log=None, chapter=None):
        """
        Takes a path to an OBS chapter and the chapter of the given file.

        :param string filename: Path to the OBS chapter file
        :param string chapter: Chapter being processed
        """
        self.filename = filename
        if not chapter:
            try:
                chapter = int(os.path.splitext(os.path.basename(filename))[0])
            except:
                chapter = None
        self.chapter = chapter
        self.log = log
        if not self.log:
            self.log = ConvertLogger()

    def run(self):
        if not self.chapter:  # skip over files that are not chapters
            return

        if not os.path.isfile(self.filename):
            self.log.warning('Chapter {0} does not exist!'.format(self.chapter))
            return

        with open(self.filename) as chapter_file:
            chapter_html = chapter_file.read()

        soup = BeautifulSoup(chapter_html, 'html.parser')

        if not soup.find('body'):
            self.log.warning('Chapter {0} has no body!'.format(self.chapter))
            return

        content = soup.body.find(id='content')

        if not content:
            self.log.warning('Chapter {0} has no content!'.format(self.chapter))
            return

        if not content.find('h1'):
            self.log.warning('Chapter {0} does not have a title!'.format(self.chapter))

        frame_count = len(content.find_all('img'))
        expected_frame_count = obs_data['chapters'][str(self.chapter).zfill(2)]['frames']
        if frame_count != expected_frame_count:
            self.log.warning(
                'Chapter {0} has only {1} frame(s).There should be {2}!'.format(self.chapter, frame_count,
                                                                                expected_frame_count))

        if len(content.find_all('p')) != (frame_count * 2 + 1):
            self.log.warning('Bible reference not found at end of chapter {0}!'.format(self.chapter))
