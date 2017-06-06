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
    elif rc.resource.identifier in ['bible', 'ulb', 'udb', 'reg']:
        preprocessor = BiblePreprocessor(rc, repo_dir, output_dir)
    elif rc.resource.identifier in ['ta']:
        preprocessor = TaPreprocessor(rc, repo_dir, output_dir)
    else:
        preprocessor = Preprocessor(rc, repo_dir, output_dir)
    return preprocessor.run()


class Preprocessor(object):
    ignoreDirectories = ['.git', '00']
    ignoreFiles = ['.DS_Store', 'reference.txt', 'title.txt', 'LICENSE.md', 'README.md']

    def __init__(self, rc, source_dir, output_dir):
        """
        :param RC rc: 
        :param string source_dir: 
        :param string output_dir: 
        """
        self.rc = rc
        self.source_dir = source_dir  # Local directory
        self.output_dir = output_dir  # Local directory

        # Write out the new manifest file based on the resource container
        write_file(os.path.join(self.output_dir, 'manifest.yaml'), self.rc.as_dict())

    def run(self):
        for project in self.rc.projects:
            content_dir = os.path.join(self.source_dir, project.path)
            # Copy all the markdown files in the project root directory to the output directory
            for file_path in glob(os.path.join(content_dir, '*.md')):
                output_file_path = os.path.join(self.output_dir, os.path.basename(file_path))
                if os.path.isfile(file_path) and not os.path.exists(output_file_path) \
                        and os.path.basename(file_path) not in self.ignoreFiles:
                    copy(file_path, output_file_path)
            for chapter in self.rc.chapters(project.identifier):
                text = ''
                for chunk in self.rc.chunks(project.identifier, chapter):
                    text += read_file(os.path.join(content_dir, chapter, chunk))+"\n\n"
                if self.rc.project_count > 1:
                    file_name = '{0}-{1}.{2}'.format(project.identifier, chapter, self.rc.resource.file_ext)
                else:
                    file_name = '{0}.{1}'.format(chapter, self.rc.resource.file_ext)
                write_file(os.path.join(self.output_dir, file_name), text)
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
        if os.path.exists(title_file):
            contents = read_file(title_file)
            title = contents.strip()
        else:
            title = chapter.lstrip('0') + '. '
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
            # Copy all the markdown files in the project root directory to the output directory
            for file_path in glob(os.path.join(content_dir, '*.md')):
                output_file_path = os.path.join(self.output_dir, os.path.basename(file_path))
                if os.path.isfile(file_path) and not os.path.exists(output_file_path) \
                        and os.path.basename(file_path) not in self.ignoreFiles:
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
            # Copy all USFM files in the project root directory to the output directory
            for file_path in glob(os.path.join(content_dir, '*.usfm')):
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


class TaPreprocessor(Preprocessor):
    manual_title_map = {
        'checking': 'Checking Manual',
        'intro': 'Introduction to translationAcademy',
        'process': 'Process Manual',
        'translate': 'Translation Manual'
    }

    def __init__(self, *args, **kwargs):
        super(TaPreprocessor, self).__init__(*args, **kwargs)

    def get_title(self, project, link, alt_title=None):
        proj = None
        if link in project.config():
            proj = project
        else:
            for p in self.rc.projects:
                if link in p.config():
                    proj = p
        if proj:
            title_file = os.path.join(self.source_dir, proj.path, link, 'title.md')
            if os.path.isfile(title_file):
                return read_file(title_file)
        if alt_title:
            return alt_title
        else:
            return link.replace('-', ' ').title()

    def get_ref(self, project, link):
        if link in project.config():
            return '#{0}'.format(link)
        for p in self.rc.projects:
            if link in p.config():
                return '{0}.html#{1}'.format(p.identifier, link)
        return '#{0}'.format(link)

    def get_question(self, project, slug):
        subtitle_file = os.path.join(self.source_dir, project.path, slug, 'sub-title.md')
        if os.path.isfile(subtitle_file):
            return read_file(subtitle_file)

    def get_content(self, project, slug):
        content_file = os.path.join(self.source_dir, project.path, slug, '01.md')
        if os.path.isfile(content_file):
            return read_file(content_file)

    def compile_section(self, project, section, level):
        """
        Recursive section markdown creator

        :param project: 
        :param dict section: 
        :param int level: 
        :return: 
        """
        if 'link' in section:
            markdown = '{0} <a name="{1}"/>{2}\n\n'.format('#'*level, section['link'], 
                                                           self.get_title(project, section['link'], section['title']))
        else:
            markdown = '{0} {1}\n\n'.format('#'*level, section['title'])
        if 'link' in section:
            link = section['link']
            question = self.get_question(project, link)
            if question:
                markdown += '*This page answers the question: {0}*\n\n'.format(question)
            config = project.config()
            if link in config:
                if 'dependencies' in config[link] and config[link]['dependencies']:
                    markdown += '*In order to understand this topic, it would be good to read:*\n\n'
                    for dependency in config[link]['dependencies']:
                        markdown += '  * [{0}]({1})\n'.\
                            format(self.get_title(project, dependency), self.get_ref(project, dependency))
                    markdown += '\n'
                content = self.get_content(project, link)
                if content:
                    markdown += '{0}\n\n'.format(content)
                if 'recommended' in config[link] and config[link]['recommended']:
                    markdown += '*Next we recommend you learn about:*\n\n'
                    for recommended in config[link]['recommended']:
                        markdown += '  * [{0}]({1})\n'.\
                            format(self.get_title(project, recommended), self.get_ref(project, recommended))
                    markdown += '\n'
                markdown += '---\n\n'  # horizontal rule
        if 'sections' in section:
            for subsection in section['sections']:
                markdown += self.compile_section(project, subsection, level + 1)
        return markdown

    def run(self):
        for project in self.rc.projects:
            toc = self.rc.toc(project.identifier)
            if project.identifier in self.manual_title_map:
                title = self.manual_title_map[project.identifier]
            else:
                title = '{0} Manual'.format(project.identifier.title())
            markdown = '# {0}\n\n'.format(title)
            for section in toc['sections']:
                markdown += self.compile_section(project, section, 2)
            markdown = self.fix_links(markdown)
            output_file = os.path.join(self.output_dir, '{0}.md'.format(project.identifier))
            write_file(output_file, markdown)

            # Copy the toc and config.yaml file to the output dir so they can be used to
            # generate the ToC on live.door43.org
            toc_file = os.path.join(self.source_dir, project.path, 'toc.yaml')
            if os.path.isfile(toc_file):
                copy(toc_file, os.path.join(self.output_dir, '{0}-toc.yaml'.format(project.identifier)))
            config_file = os.path.join(self.source_dir, project.path, 'config.yaml')
            if os.path.isfile(config_file):
                copy(config_file, os.path.join(self.output_dir, '{0}-config.yaml'.format(project.identifier)))
        return True

    @staticmethod
    def fix_links(content):
        # fix links to other sections within the same manual (only one ../ and a section name)
        # e.g. [Section 2](../section2/01.md) => [Section 2](#section2)
        content = re.sub(r'\]\(\.\./([^/\)]+)/01.md\)', r'](#\1)', content)
        # fix links to other manuals (two ../ and a manual name and a section name)
        # e.g. [how to translate](../../translate/accurate/01.md) => [how to translate](translate.html#accurate)
        content = re.sub(r'\]\(\.\./\.\./([^/\)]+)/([^/\)]+)/01.md\)', r'](\1.html#\2)', content)
        # fix links to other sections that just have the section name but no 01.md page (preserve http:// links)
        # e.g. See [Verbs](figs-verb) => See [Verbs](#figs-verb)
        content = re.sub(r'\]\(([^# :/\)]+)\)', r'](#\1)', content)
        # convert URLs to links if not already
        content = re.sub(r'([^"\(])((http|https|ftp)://[A-Z0-9\/\?&_\.:=#-]+[A-Z0-9\/\?&_:=#-])', r'\1[\2](\2)', content, flags=re.IGNORECASE)
        # URLS wth just www at the start, no http
        content = re.sub(r'([^A-Z0-9"\(\/])(www\.[A-Z0-9\/\?&_\.:=#-]+[A-Z0-9\/\?&_:=#-])', r'\1[\2](http://\2)', content, flags=re.IGNORECASE)
        return content
