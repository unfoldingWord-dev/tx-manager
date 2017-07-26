from __future__ import print_function, unicode_literals
import os
from bs4 import BeautifulSoup
from libraries.checkers.checker import Checker
from libraries.checkers.obs_data import obs_data
from libraries.general_tools.file_utils import read_file


class ObsChecker(Checker):

    def run(self):
        """
        Checks for issues with OBS

        Use self.log.warning("message") to log any issues.
        self.preconvert_dir is the directory of pre-converted files
        self.converted_dir is the directory of converted files
        :return:
        """
        for chapter in range(1, 51):
            filename = os.path.join(self.converted_dir, str(chapter).zfill(2)+'.html')

            if not os.path.isfile(filename):
                self.log.warning('Chapter {0} does not exist!'.format(chapter))
                continue

            chapter_html = read_file(filename)
            soup = BeautifulSoup(chapter_html, 'html.parser')

            if not soup.find('body'):
                self.log.warning('Chapter {0} has no body!'.format(chapter))
                return

            content = soup.body.find(id='content')

            if not content:
                self.log.warning('Chapter {0} has no content!'.format(chapter))
                return

            if not content.find('h1'):
                self.log.warning('Chapter {0} does not have a title!'.format(chapter))

            frame_count = len(content.find_all('img'))
            expected_frame_count = obs_data['chapters'][str(chapter).zfill(2)]['frames']
            if frame_count != expected_frame_count:
                self.log.warning(
                    'Chapter {0} has only {1} frame(s).There should be {2}!'.format(chapter, frame_count,
                                                                                    expected_frame_count))

            if len(content.find_all('p')) != (frame_count * 2 + 1):
                self.log.warning('Bible reference not found at end of chapter {0}!'.format(chapter))
