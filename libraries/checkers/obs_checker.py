from __future__ import print_function, unicode_literals
import os

import re
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
        for chapter in range( 1, 51 ):
            chapter_number = str(chapter).zfill(2)                                       # chapter check
            filename = os.path.join(self.preconvert_dir, chapter_number + '.md')

            if not os.path.isfile(filename):
                self.log.warning('Chapter {0} does not exist!'.format(chapter_number))
                continue

            chapter_md = read_file(filename)
            is_title = chapter_md.find('# ')

            if is_title < 0:                                                             # Find chapter headings
                self.log.warning('Chapter {0} does not have a title!'.format(chapter_number))

            expected_frame_count = obs_data['chapters'][str(chapter).zfill(2)]['frames'] # Identify missing frames

            for frame_idx in range( 1, expected_frame_count ):
                frame_index = str(frame_idx).zfill(2)
                pattern = '-{0}-{1}.'.format(chapter_number, frame_index)

                if chapter_md.find( pattern ) < 0:
                    self.log.warning('Missing frame: {0}-{1}'.format(chapter_number, frame_index))


            if re.search( r'^_.*:.*_[ ]*$', chapter_md, re.M ) == None:                                     # look for verse reference
                self.log.warning('Bible reference not found at end of chapter {0}!'.format(chapter_number))

        for book_end in [ 'front', 'back' ]:                                         # misssing back matter
            filename = os.path.join(self.preconvert_dir, book_end + '.md')

            lines = { 'front': 'The licensor cannot revoke',
                      'back':  'We want to make this visual'}

            if not os.path.isfile(filename):
                self.log.warning('Chapter {0} does not exist!'.format(book_end))
                continue

            end_content = read_file( filename )
            pat = lines[book_end]

            if end_content.find( pat ) >= 0:
                self.log.warning('Story {0} matter is not translated!'.format(book_end) )
