from __future__ import unicode_literals
import os
import re
from door43_tools.td_language import TdLanguage
from door43_tools.bible_books import BOOK_NAMES
from general_tools.file_utils import load_json_object, load_yaml_object, read_file
from datetime import datetime
from glob import glob

resource_map = {
    'udb': {
        'title': 'Unlocked Dynamic Bible',
        'type': 'book',
        'format': 'text/usfm'
    },
    'ulb': {
        'title': 'Unlocked Literal Bible',
        'type': 'book',
        'format': 'text/usfm'
    },
    'bible': {
        'title': 'Unlocked Bible',
        'type': 'book',
        'format': 'text/usfm'
    },
    'obs': {
        'title': 'Open Bible Stories',
        'type': 'book',
        'format': 'text/markdown'
    },
    'tn': {
        'title': 'translationNotes',
        'type': 'help',
        'format': 'text/markdown'
    },
    'tw': {
        'title': 'translationWords',
        'type': 'dict',
        'format': 'text/markdown'
    },
    'tq': {
        'title': 'translationQuestions',
        'type': 'help',
        'format': 'text/markdown'
    },
    'ta': {
        'title': 'translationAcademy',
        'type': 'man',
        'format': 'text/markdown'
    }
}


class RC:
    current_version = '0.2'

    def __init__(self, directory, repo_name=None):
        """
        :param string directory:
        """
        self.dir = directory
        self._resource = None
        self._projects = []
        self._repo_name = repo_name

        if not isinstance(self.dir, str) and not isinstance(self.dir, unicode):
            raise Exception('Missing string parameter: dir')

        if not os.path.isdir(self.dir):
            raise Exception('Directory doesn\'t exist: {0}'.format(self.dir))

        self.manifest = load_yaml_object(os.path.join(self.dir, 'manifest.yaml'))
        if not self.manifest:
            self.manifest = load_json_object(os.path.join(self.dir, 'manifest.json'))
        if not self.manifest:
            self.manifest = load_json_object(os.path.join(self.dir, 'package.json'))
        if not self.manifest:
            self.manifest = load_json_object(os.path.join(self.dir, 'project.json'))
        if not self.manifest:
            self.manifest = load_json_object(os.path.join(self.dir, 'meta.json'))
        if not self.manifest:
            self.manifest = manifest_from_repo_name(self.repo_name)

    def as_dict(self):
        """
        Return a proper dict object of the manifest
        :return dict: 
        """
        return {
            'dublin_core': {
                'type': self.resource.type,
                'conformsto': self.resource.conformsto,
                'format': self.resource.format,
                'identifier': self.resource.identifier,
                'title': self.resource.title,
                'subject': self.resource.subject,
                'description': self.resource.description,
                'language': {
                    'identifier': self.resource.language.identifier,
                    'title': self.resource.language.title,
                    'direction': self.resource.language.direction
                },
                'source': self.resource.source,
                'rights': self.resource.rights,
                'creator': self.resource.creator,
                'contributor': self.resource.contributor,
                'relation': self.resource.relation,
                'publisher': self.resource.publisher,
                'issued': self.resource.issued,
                'modified': self.resource.modified,
                'version': self.resource.version
            },
            'checking': {
                'checking_entity': self.checking_entity,
                'checking_level': self.checking_level
            },
            'projects': self.projects_as_dict
        }

    @property
    def path(self):
        return self.dir

    @property
    def repo_name(self):
        if self._repo_name:
            return self._repo_name
        else:
            path = self.path.rstrip('/')
            return os.path.basename(path)

    @property
    def resource(self):
        if not self._resource:
            if 'dublin_core' in self.manifest and self.manifest['dublin_core']:
                self._resource = Resource(self, self.manifest['dublin_core'])
            elif 'resource' in self.manifest and self.manifest['resource']:
                resource = self.manifest['resource']
                if len(resource) == 2 and 'id' in resource and 'name' in resource:
                    self.manifest['id'] = resource['id']
                    self.manifest['name'] = resource['name']
                    resource = self.manifest
                self._resource = Resource(self, resource)
            else:
                self._resource = Resource(self, self.manifest)
        return self._resource

    @property
    def checking_entity(self):
        return self.manifest.get('checking', {}).get('checking_entity', ['Wycliffe Associates'])

    @property
    def checking_level(self):
        return self.manifest.get('checking', {}).get('checking_level', '1')

    @property
    def projects(self):
        if not self._projects:
            if 'projects' in self.manifest and len(self.manifest['projects']):
                for p in self.manifest['projects']:
                    project = Project(self, p)
                    if os.path.join(self.dir, project.path):
                        self._projects.append(project)
            elif 'project'in self.manifest:
                project = Project(self, self.manifest['project'])
                if os.path.join(self.dir, project.path):
                    self._projects.append(project)
            if not len(self._projects):
                self._projects.append(Project(self, {}))  # will rely on info in the resource
        return self._projects

    @property
    def projects_as_dict(self):
        projects = []
        for project in self.projects:
            projects.append(project.as_dict())
        return projects

    def project(self, identifier=None):
        """
        Retrieves a project from the RC.

        You can exclude the parameter if the RC only has one project.

        :param identifier:
        :return:
        """
        if identifier:
            for p in self.projects:
                if p.identifier == identifier:
                    return p
        else:
            if len(self.projects) == 1:
                return self.projects[0]
            elif len(self.projects) > 1:
                raise Exception('Multiple projects found. Specify the project identifier.')

    @property
    def project_count(self):
        return len(self.projects)

    @property
    def project_ids(self):
        identifiers = []
        for p in self.projects:
            identifiers.append(p.identifier)
        return identifiers

    def chapters(self, identifier=None):
        """
        Returns an array of chapters in the project of the given identifier.
        You can exclude the parameter if this RC only has one project.
        :param identifier: The project identifier
        :return array:
        """
        p = self.project(identifier)
        if p is None:
            return []
        else:
            chapters = []
            for d in sorted(glob(os.path.join(self.dir, p.path, '*'))):
                chapter = os.path.basename(d)
                if os.path.isdir(d) and not chapter.startswith('.'):
                    if len(self.chunks(identifier, chapter)):
                        chapters.append(chapter)
            return chapters

    def chunks(self, project_identifier, chapter_identifier=None):
        if chapter_identifier is None:
            chapter_identifier = project_identifier
            project_identifier = 0
        p = self.project(project_identifier)
        if p is None:
            return []
        chunks = []
        for f in sorted(glob(os.path.join(self.dir, p.path, chapter_identifier, '*'))):
            chunk = os.path.basename(f)
            ext = os.path.splitext(chunk)[1]
            if os.path.isfile(f) and not chunk.startswith('.') and ext in ['', '.txt', '.text', '.md', '.usfm']:
                chunks.append(chunk)
        return chunks

    def usfm_files(self, identifier=None):
        """
        Returns an array of .usfm files in the project directory. Mainly used to determine if type is a bundle.
        You can exclude the parameter if this RC only has one project.
        :param identifier: The project identifier
        :return array:
        """
        p = self.project(identifier)
        if p is None:
            return []
        else:
            usfm_files = []
            for f in glob(os.path.join(self.dir, p.path, '*.usfm')):
                usfm_files.append(os.path.basename(f))
            return usfm_files

    def config(self, project_identifier=None):
        p = self.project(project_identifier)
        if p is None:
            return None
        if not p.config_yaml:
            file_path = os.path.join(self.dir, p.path, 'config.yaml')
            p.config_yaml = load_yaml_object(file_path)
        return p.config_yaml

    def toc(self, project_identifier=None):
        p = self.project(project_identifier)
        if p is None:
            return None
        if not p.toc_yaml:
            file_path = os.path.join(self.dir, p.path, 'toc.yaml')
            p.toc_yaml = load_yaml_object(file_path)
        return p.toc_yaml


class Resource:
    def __init__(self, rc, resource):
        """
        :param RC rc: 
        :param dict resource: 
        """
        self.rc = rc
        self.resource = resource
        if not isinstance(self.resource, dict):
            raise Exception('Missing dict parameter: resource')
        self._language = None

    @property
    def conformsto(self):
        return self.resource.get('conformsto', 'pre-rc')

    @property
    def format(self):
        if 'format' in self.resource and self.resource['format']:
            old_format = self.resource['format']
            if '/' not in old_format:
                return 'text/{0}'.format(old_format.lower())
            return old_format
        elif 'content_mime_type' in self.resource and self.resource['content_mime_type']:
            return self.resource['content_mime_type']
        elif self.identifier in resource_map:
            return resource_map[self.identifier]['format']

    @property
    def file_ext(self):
        """
        File extension of this type of resource, such as md or usfm
        :return string: 
        """
        return {
            'text/usx': 'usx',
            'text/usfm': 'usfm',
            'text/markdown': 'md'
        }.get(self.format, 'txt')

    @property
    def type(self):
        if 'type' in self.resource and isinstance(self.resource['type'], basestring):
            return self.resource['type']
        elif self.identifier in ['udb', 'ulb', 'bible']:
            if len(self.rc.usfm_files()):
                return 'bundle'
            else:
                return resource_map[self.identifier]['type']
        elif self.identifier in resource_map:
            return resource_map[self.identifier]['type']
        else:
            return 'book'

    @property
    def identifier(self):
        if 'identifier' in self.resource and self.resource['identifier']:
            return self.resource['identifier']
        if 'id' in self.resource and self.resource['id']:
            return self.resource['id']
        elif 'slug' in self.resource and self.resource['slug']:
            slug = self.resource['slug']
            if 'ulb' in slug:
                return 'ulb'
            elif 'udb' in slug:
                return 'udb'
            elif 'obs' in slug:
                return 'obs'
            else:
                return slug
        elif 'ulb' in self.rc.repo_name:
            return 'ulb'
        elif 'udb' in self.rc.repo_name:
            return 'udb'
        elif 'obs' in self.rc.repo_name:
            return 'obs'
        else:
            return 'bible'

    @property
    def title(self):
        if 'title' in self.resource and self.resource['title']:
            return self.resource['title']
        elif 'name' in self.resource and self.resource['name']:
            return self.resource['name']
        elif self.identifier in resource_map:
            return resource_map[self.identifier]['title']
        else:
            return self.identifier

    @property
    def subject(self):
        return self.resource.get('subject', self.title)

    @property
    def description(self):
        return self.resource.get('description', self.title)

    @property
    def relation(self):
        return self.resource.get('relation', [])

    @property
    def publisher(self):
        return self.resource.get('publisher', 'Door43')

    @property
    def issued(self):
        if 'issued' in self.resource and self.resource['issued']:
            return self.resource.get('issued')
        elif 'pub_date' in self.resource.get('status', {}):
            return self.resource['status']['pub_date']
        else:
            return datetime.utcnow().strftime("%Y-%m-%d")

    @property
    def modified(self):
        return self.resource.get('modified', datetime.utcnow().strftime("%Y-%m-%d"))

    @property
    def rights(self):
        return self.resource.get('rights', 'CC BY-SA 4.0')

    @property
    def creator(self):
        return self.resource.get('creator', 'Wycliffe Associates')

    @property
    def language(self):
        if not self._language:
            if 'language'in self.resource:
                self._language = Language(self.rc, self.resource['language'])
            elif 'target_language' in self.resource and self.resource['target_language']:
                self._language = Language(self.rc, self.resource['target_language'])
            elif 'target_language' in self.rc.manifest and self.rc.manifest['target_language']:
                self._language = Language(self.rc, self.rc.manifest['target_language'])
            else:
                self._language = Language(self.rc, {
                    'identifier': 'en',
                    'title': 'English',
                    'direction': 'ltr'
                })
        return self._language

    @property
    def contributor(self):
        if 'contributor' in self.resource and self.resource['contributor']:
            return self.resource['contributor']
        elif 'translators' in self.resource and self.resource['translators']:
            contributor = []
            for translator in self.resource['translators']:
                if isinstance(translator, dict) and 'name' in translator:
                    contributor.append(translator['name'])
                elif isinstance(translator, basestring):
                    contributor.append(translator)
            return contributor
        else:
            return []

    @property
    def source(self):
        if 'source' in self.resource and self.resource['source']:
            return self.resource['source']
        else:
            sts = None
            if 'source_translations' in self.resource and self.resource['source_translations']:
                sts = self.resource['source_translations']
            elif 'source_translations' in self.resource.get('status', {}):
                sts = self.resource['status']['source_translations']
            if sts:
                sources = []
                for st in sts:
                    source = {}
                    if 'resource_id' in st and st['resource_id']:
                        source['identifier'] = st['resource_id']
                    elif 'resource_slug' in st and st['resource_slug']:
                        source['identifier'] = st['resource_slug']
                    if 'language_id' in st and st['language_id']:
                        source['language'] = st['language_id']
                    elif 'language_slug' in st and st['language_slug']:
                        source['language'] = st['language_slug']
                    if 'version' in st and st['version']:
                        source['version'] = st['version']
                    if source:
                        sources.append(source)
                return sources
            else:
                return []

    @property
    def version(self):
        return self.resource.get('version', '1')


class Language:
    def __init__(self, rc, language):
        """
        :param RC rc: 
        :param dict language: 
        """
        self.rc = rc
        self.language = language
        if not isinstance(self.language, dict):
            raise Exception('Missing dict parameter: language')

    @property
    def identifier(self):
        if 'identifier' in self.language and self.language['identifier']:
            return self.language['identifier']
        elif 'slug' in self.language and self.language['slug']:
            return self.language['slug']
        elif 'id' in self.language and self.language['id']:
            return self.language['id']
        else:
            return 'en'

    @property
    def direction(self):
        if 'direction'in self.language:
            return self.language['direction']
        if 'dir'in self.language:
            return self.language['dir']
        else:
            return 'ltr'

    @property
    def title(self):
        if 'title'in self.language:
            return self.language['title']
        elif 'name'in self.language:
            return self.language['name']
        else:
            return 'English'


class Project:
    def __init__(self, rc, project):
        """
        :param RC rc: 
        :param dict project: 
        """
        self.rc = rc
        self.project = project
        if not isinstance(self.rc, RC):
            raise Exception('Missing RC parameter: rc')
        if not isinstance(self.project, dict):
            raise Exception('Missing dict parameter: project')
        self.config_yaml = None
        self.toc_yaml = None

    @property
    def identifier(self):
        if 'identifier'in self.project:
            return self.project['identifier'].lower()
        elif 'id'in self.project:
            return self.project['id'].lower()
        elif 'project_id' in self.project and self.project['project_id']:
            return self.project['project_id'].lower()
        else:
            return self.rc.resource.identifier

    @property
    def title(self):
        if 'title'in self.project and self.project['title']:
            return self.project['title']
        elif 'name'in self.project and self.project['name']:
            return self.project['name']
        elif os.path.isfile(os.path.join(self.rc.path, self.path, 'title.txt')):
            self.project['title'] = read_file(os.path.join(self.rc.path, self.path, 'title.txt'))
            return self.project['title']
        elif os.path.isfile(os.path.join(self.rc.path, 'title.txt')):
            self.project['title'] = read_file(os.path.join(self.rc.path, 'title.txt'))
            return self.project['title']
        else:
            return self.rc.resource.title

    @property
    def path(self):
        if 'path' in self.project and self.project['path']:
            return self.project['path']
        elif os.path.isdir(os.path.join(self.rc.dir, './content')):
                return './content'
        else:
            return './'

    @property
    def sort(self):
        return self.project.get('sort', '1')

    @property
    def versification(self):
        return self.project.get('versification', 'kjv')

    @property
    def categories(self):
        return self.project.get('categories', [])

    def toc(self):
        return self.rc.toc(self.identifier)

    def config(self):
        return self.rc.config(self.identifier)

    def chapters(self):
        return self.rc.chapters(self.identifier)

    def chunks(self, chapter_identifier=None):
        return self.rc.chunks(self.identifier, chapter_identifier)

    def usfm_files(self):
        return self.rc.usfm_files(self.identifier)

    def as_dict(self):
        return {
            'categories': self.categories,
            'identifier': self.identifier,
            'path': self.path,
            'sort': self.sort,
            'title': self.title,
            'versification': self.versification
        }


def manifest_from_repo_name(repo_name):
    manifest = {
        'dublin_core': {},
    }

    parts = re.findall(r'[A-Za-z0-9]+', repo_name)

    for i, part in enumerate(parts):
        if part == 'en':
            # Speeds things up for English repos
            manifest['dublin_core']['language'] = {
                'identifier': 'en',
                'title': 'English',
                'direction': 'ltr'
            }
            continue
        else:
            lang = TdLanguage.get_language(part)
            if lang and 'language' not in manifest['dublin_core']:
                manifest['dublin_core']['language'] = {
                    'identifier': lang.lc,
                    'title': lang.ln,
                    'direction': lang.ld
                }
                continue

        if part.lower() in resource_map:
            manifest['dublin_core']['identifier'] = part
            if 'projects' not in manifest:
                manifest['projects'] = [{'identifier': part}]
            continue

        if part.lower() in BOOK_NAMES:
            project = {
                'identifier': part.lower(),
                'title': BOOK_NAMES[part.lower()]
            }
            if 'identifier' not in manifest['dublin_core']:
                manifest['dublin_core']['identifier'] = 'bible'
            if 'projects' not in manifest:
                manifest['projects'] = []
            manifest['projects'].append(project)
            continue

    if 'identifier' not in manifest['dublin_core']:
        manifest['dublin_core']['identifier'] = repo_name

    return manifest
