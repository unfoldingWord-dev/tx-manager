from __future__ import print_function, unicode_literals
import os
import re
from libraries.linters.markdown_linter import MarkdownLinter
from libraries.linters.obs_data import obs_data
from libraries.general_tools.file_utils import read_file


class ObsLinter(MarkdownLinter):

    def lint(self):
        """
        Checks for issues with OBS

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of .md files
        :return bool:
        """
        # chapter check
        print(self.rc.project())
        print(self.rc.project().path)
        project_dir = os.path.join(self.source_dir, self.rc.project().path)
        for chapter in range(1, 51):
            chapter_number = str(chapter).zfill(2)
            filename = os.path.join(project_dir, chapter_number + '.md')

            if not os.path.isfile(filename):
                self.log.warning('Chapter {0} does not exist!'.format(chapter_number))
                continue

            chapter_md = read_file(filename)
            is_title = chapter_md.find('# ')

            # Find chapter headings
            if is_title < 0:
                self.log.warning('Chapter {0} does not have a title!'.format(chapter_number))

            # Identify missing frames
            expected_frame_count = obs_data['chapters'][str(chapter).zfill(2)]['frames']

            for frame_idx in range(1, expected_frame_count):
                frame_index = str(frame_idx).zfill(2)
                pattern = '-{0}-{1}.'.format(chapter_number, frame_index)

                if chapter_md.find(pattern) < 0:
                    self.log.warning('Missing frame: {0}-{1}'.format(chapter_number, frame_index))

            # look for verse reference
            if not re.search(r'^_.*:.*_[ ]*$', chapter_md, re.M):
                self.log.warning('Bible reference not found at end of chapter {0}!'.format(chapter_number))

        # Check front and back matter
        for book_end in ['front', 'back']:
            filename = os.path.join(project_dir, book_end, 'intro.md')
            if not os.path.isfile(filename):
                filename = os.path.join(project_dir, '{0}.md'.format(book_end))

            lines = {
                'front': 'The licensor cannot revoke',
                'back':  'We want to make this visual'
            }

            if not os.path.isfile(filename):
                self.log.warning('{0}.md does not exist!'.format(book_end))
                continue

            if self.rc.resource.language.identifier != 'en':
                end_content = read_file(filename)
                if lines[book_end] in end_content:
                    self.log.warning('Story {0} matter is not translated!'.format(book_end) )

        return super(ObsLinter, self).lint()  # Runs the markdown linter

