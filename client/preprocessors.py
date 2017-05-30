from __future__ import unicode_literals, print_function
import os
import re
from door43_tools import bible_books
from general_tools.file_utils import write_file, read_file
from shutil import copy
from resource_container.ResourceContainer import RC
from glob import glob


def do_preprocess(rc, repo_dir, output_dir):
    if rc.resource.identifier in ['obs']:
        preprocessor = ObsPreprocessor(rc, repo_dir, output_dir)
    elif rc.resource.identifier in ['bible', 'ulb', 'udb']:
        preprocessor = BiblePreprocessor(rc, repo_dir, output_dir)
    else:
        preprocessor = Preprocessor(rc, repo_dir, output_dir)
    return preprocessor.run()


class Preprocessor(object):
    ignoreDirectories = ['.git', '00']
    ignoreFiles = ['.DS_Store', 'reference.txt', 'title.txt']

    def __init__(self, rc, source_dir, output_dir, quiet=False):
        """
        :param RC rc: 
        :param string source_dir: 
        :param string output_dir: 
        :param bool quiet: 
        """
        self.rc = rc
        self.source_dir = source_dir  # Local directory
        self.output_dir = output_dir  # Local directory
        self.quiet = quiet

        # Copy all files in the root of source_dir
        for file_path in glob(self.source_dir+"/*"):
            if os.path.isfile(file_path):
                copy(file_path, self.output_dir)

        # Write out the new manifest file based on the resource container
        write_file(os.path.join(self.output_dir, 'manifest.json'), self.rc.as_dict())

    def run(self):
        for project in self.rc.projects:
            content_dir = os.path.join(self.source_dir, project.path)
            # Copy all files in the project directory
            for file_path in glob(os.path.join(content_dir, "*")):
                output_file_path = os.path.join(self.output_dir, os.path.basename(file_path))
                if os.path.isfile(file_path) and not os.path.exists(output_file_path):
                    copy(file_path, output_file_path)
            for chapter in self.rc.chapters(project.identifier):
                text = ''
                for chunk in self.rc.chunks(project.identifier, chapter):
                    text += read_file(os.path.join(content_dir, chapter, chunk))+"\n"
                write_file(os.path.join(self.output_dir, '{0}.{1}'.format(chapter, self.rc.resource.file_ext)), text)
        return True


class ObsPreprocessor(Preprocessor):
    def __init__(self, *args, **kwargs):
        super(ObsPreprocessor, self).__init__(*args, **kwargs)

    @staticmethod
    def get_chapters(content_dir):
        chapters = []
        for chapter in sorted(os.listdir(content_dir)):
            if os.path.isdir(os.path.join(content_dir, chapter)) and chapter not in ObsPreprocessor.ignoreDirectories:
                chapters.append({
                    'id': chapter,
                    'title': ObsPreprocessor.get_chapter_title(content_dir, chapter),
                    'reference': ObsPreprocessor.get_chapter_reference(content_dir, chapter),
                    'frames': ObsPreprocessor.get_chapter_frames(content_dir, chapter)
                })
        return chapters

    @staticmethod
    def get_chapter_title(content_dir, chapter):
        """
        Get a chapter title.
        if the title file does not exist, it will hand back the number with a period only.
        """
        title_file = os.path.join(content_dir, chapter, 'title.txt')
        title = chapter.lstrip('0') + '. '
        if os.path.exists(title_file):
            contents = read_file(title_file)
            title = contents.strip()
        return title

    @staticmethod
    def get_chapter_reference(content_dir, chapter):
        """Get the chapters reference text"""
        reference_file = os.path.join(content_dir, chapter, 'reference.txt')
        reference = ''
        if os.path.exists(reference_file):
            contents = read_file(reference_file)
            reference = contents.strip()
        return reference

    @staticmethod
    def get_chapter_frames(content_dir, chapter):
        frames = []
        chapter_dir = os.path.join(content_dir, chapter)
        for frame in sorted(os.listdir(chapter_dir)):
            if frame not in ObsPreprocessor.ignoreFiles:
                text = read_file(os.path.join(content_dir, chapter, frame))
                frames.append({
                    'id': chapter + '-' + frame.strip('.txt'),
                    'text': text
                })
        return frames

    def is_chunked(self, project):
        chapters = self.rc.chapters(project.identifier)
        if chapters and len(chapters):
            chunks = self.rc.chunks(project.identifier, chapters[0])
            for chunk in chunks:
                if os.path.basename(chunk) in ['title.txt', 'reference.txt', '01.txt']:
                    return True
        return False

    def run(self):
        for project in self.rc.projects:
            content_dir = os.path.join(self.source_dir, project.path)
            # Copy all files in the project directory
            for file_path in glob(os.path.join(content_dir, "*")):
                output_file_path = os.path.join(self.output_dir, os.path.basename(file_path))
                if os.path.isfile(file_path) and not os.path.exists(output_file_path):
                    copy(file_path, output_file_path)
            if self.is_chunked(project):
                for chapter in self.get_chapters(content_dir):
                    markdown = '# {0}\n\n'.format(chapter['title'])
                    for frame in chapter['frames']:
                        markdown += '![Frame {0}](https://cdn.door43.org/obs/jpg/360px/obs-en-{0}.jpg)\n\n' \
                            .format(frame.get('id'))
                        markdown += frame['text'] + '\n\n'
                    markdown += '_{0}_\n'.format(chapter['reference'])
                    output_file = os.path.join(self.output_dir, '{0}.md'.format(chapter.get('id')))
                    write_file(output_file, markdown)
            else:
                for chapter in self.rc.chapters(project.identifier):
                    f = None
                    if os.path.isfile(os.path.join(content_dir, chapter, "01.md")):
                        f = os.path.join(content_dir, chapter, '01.md')
                    elif os.path.isfile(os.path.join(content_dir, chapter, 'intro.md')):
                        f = os.path.join(content_dir, chapter, 'intro.md')
                    if f:
                        copy(f, os.path.join(self.output_dir, '{0}.md'.format(chapter)))
        return True


class BiblePreprocessor(Preprocessor):
    def __init__(self, *args, **kwargs):
        super(BiblePreprocessor, self).__init__(*args, **kwargs)

    def run(self):
        for project in self.rc.projects:
            content_dir = os.path.join(self.source_dir, project.path)
            # Copy all files in the project directory as it may just have 01-GEN.usfm, etc.
            for file_path in glob(os.path.join(content_dir, "*")):
                output_file_path = os.path.join(self.output_dir, os.path.basename(file_path))
                if os.path.isfile(file_path) and not os.path.exists(output_file_path):
                    copy(file_path, output_file_path)
            # Look to see if there are chapters and if so, build the USFM file
            chapters = self.rc.chapters(project.identifier)
            if len(chapters):
                title_file = os.path.join(content_dir, chapters[0], 'title.txt')
                if os.path.isfile(title_file):
                    title = read_file(title_file)
                    title = re.sub(r' \d+$', '', title).strip()
                else:
                    title = project.title
                if not title and os.path.isfile(os.path.join(content_dir, 'title.txt')):
                    title = read_file(os.path.join(content_dir, 'title.txt'))
                usfm = """
\\id {0} {1}
\\ide UTF-8
\\h {2}
\\toc1 {2}
\\toc2 {2}
\\mt {2}
""".format(project.identifier.upper(), self.rc.resource.title, title)
                for chapter in chapters:
                    if chapter in self.ignoreDirectories:
                        continue
                    chapter_num = chapter.lstrip('0')
                    chunks = self.rc.chunks(project.identifier, chapter)
                    if not len(chunks):
                        continue
                    first_chunk = read_file(os.path.join(content_dir, chapter, chunks[0]))
                    usfm += "\n\n"
                    if '\\c {0}'.format(chapter_num) not in first_chunk:
                        usfm += "\\c {0}\n".format(chapter_num)
                    if os.path.isfile(os.path.join(content_dir, chapter, 'title.txt')):
                        translated_title = read_file(os.path.join(content_dir, chapter, 'title.txt'))
                        book_name = re.sub(r' \d+$', '', translated_title).strip()
                        if book_name.lower() != title.lower():
                            usfm += "\cl {0}\n".format(translated_title)
                    for chunk in chunks:
                        if chunk in self.ignoreFiles:
                            continue
                        chunk_num = os.path.splitext(chunk)[0].lstrip('0')
                        chunk_content = read_file(os.path.join(content_dir, chapter, chunk))
                        if '\\v {0} '.format(chunk_num) not in chunk_content:
                            chunk_content = '\\v {0} '.format(chunk_num) + chunk_content
                        usfm += chunk_content+"\n"

                usfm_file = os.path.join(self.output_dir,
                                         '{0}-{1}.usfm'.format(bible_books.BOOK_NUMBERS[project.identifier],
                                                               project.identifier.upper()))
                write_file(usfm_file, usfm)
        return True
