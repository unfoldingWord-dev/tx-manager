from __future__ import print_function, unicode_literals
import os
from six import iteritems
from glob import glob
from datetime import datetime
from door43_tools.bible_books import BOOK_NAMES, BOOK_NUMBERS
from door43_tools.language_handler import Language
from general_tools.file_utils import load_json_object, get_files, get_subdirs


class Manifest(object):
    LATEST_VERSION = 6

    def __init__(self, file_name=None, meta=None, repo_name=None, files_path=None):
        """
        Class constructor. Optionally accepts the name of a file to deserialize.
        :param str file_name: The name of a file to deserialize into a Manifest object
        """
        # Defaults
        self.package_version = Manifest.LATEST_VERSION
        self.format = ""
        self.generator = {
            "name": "",
            "build": ""
        }
        self.target_language = {
            "id": "",
            "name": "",
            "direction": "ltr"
        }
        self.project = {
            "id": "",
            "name": ""
        }
        self.type = {
            "id": "text",
            "name": "Text"
        }
        self.resource = {
            "id": "",
            "name": ""
        }
        self.source_translations = []
        self.parent_draft = {}
        self.translators = []
        self.finished_chunks = []

        # deserialize
        if file_name:
            if os.path.isfile(file_name):
                manifest_json = load_json_object(file_name)
                manifest_json = Manifest.standardize_manifest_json(manifest_json)
                self.__dict__.update(manifest_json)
            else:
                raise IOError('The file {0} was not found.'.format(file_name))
        if meta:
            self.update_from_meta(meta)
        if files_path:
            self.update_from_files(files_path)
        if repo_name:
            self.update_from_repo_name(repo_name)

        if not self.resource['id'] and (self.format == 'usfm' or (self.project['id'] and self.project['id'].lower() in BOOK_NAMES)):
            self.resource['id'] = 'bible'
            self.resource['name'] = 'Bible'

    def update_from_meta(self, meta):
        if meta.lang and not self.target_language['id']:
            languages = Language.load_languages()
            found = [x for x in languages if x.lc == meta.lang]
            name = meta.lang
            if len(found) > 0:
                name = found[0].ln
            self.target_language = {'id': meta.lang, 'name': name}
            del meta.lang
        if meta.name and not self.project['name']:
            self.project['name'] = meta.name
            del meta.name
        if meta.contributors and not self.translators:
            self.translators = meta.contributors.split(', ')
            del meta.contributors
        if meta.slug:
            self.update_from_repo_name(meta.slug)
        for key, value in iteritems(meta.__dict__):
            if value and not hasattr(self, key):
                setattr(self, key, value)

    def update_from_repo_name(self, repo_name):
        if '_' in repo_name:
            parts = repo_name.split('_')
        else:
            parts = repo_name.split('-')

        if not self.target_language['id']:
            languages = Language.load_languages()
            for i, part in enumerate(parts):
                found = [x for x in languages if x.lc == part]
                if len(found):
                    lang = found[0]
                    self.target_language['id'] = lang.lc
                    self.target_language['name'] = lang.ln
                    self.target_language['direction'] = lang.ld
                del parts[i]
                break

        for part in parts:
            if not self.resource['id']:
                if part.lower() == 'obs':
                    self.resource['id'] = 'obs'
                elif part.lower() == 'ulb':
                    self.resource['id'] = 'ulb'
                elif part.lower() == 'udb':
                    self.resource['id'] = 'udb'
                elif part.lower() == 'bible':
                    self.resource['id'] = 'bible'
                self.resource['name'] = Manifest.get_resource_name(self.resource['id'])
            if not self.format:
                if part.lower() == 'obs':
                    self.format = 'markdown'
                if part.lower() == 'ulb' or part.lower() == 'udb' or part.lower() == 'bible':
                    self.format = 'usfm'

            if not self.project['id'] and part.lower() in BOOK_NAMES:
                self.project['id'] = part.lower()
                self.project['name'] = BOOK_NAMES[part.lower()]
                if not self.format:
                    self.format = 'usfm'
                if not self.resource['id']:
                    self.resource['id'] = 'bible'
                    self.resource['name'] = 'Bible'

        if not self.resource['id']:
            self.resource['id'] = repo_name
            self.resource['name'] = repo_name

        if not self.target_language['id']:
            self.target_language['id'] = 'en'
            self.target_language['name'] = 'English'

    def update_from_files(self, path):
        path = path.rstrip('/')

        found_markdown = False
        found_usfm = False
        found_html = False
        found_text_in_numbered_dir = False

        if not self.format:
            for f in get_files(path):
                if f.endswith('usfm'):
                    found_usfm = True
                elif f.endswith('.md'):
                    found_markdown = True
                elif f.endswith('.html'):
                    found_html = True
                elif f.endswith('.txt'):
                    try:
                        if int(os.path.basename(os.path.dirname(f))):
                            found_text_in_numbered_dir = True
                    except Exception:
                        pass
        if found_usfm:
            if not self.format:
                self.format = 'usfm'
            if not self.resource['id']:
                self.resource['id'] = 'bible'
                self.resource['name'] = 'Bible'
        elif found_markdown:
            if not self.format:
                self.format = 'markdown'
        elif found_html:
            if not self.format:
                self.format = 'html'

        if not self.generator['name']:
            for subdir in glob(os.path.join(path, '*')):
                if os.path.isdir(subdir):
                    dir_name = subdir[len(path)+1:]
                    try:
                        if int(dir_name) and len(glob(os.path.join(subdir, '*.txt'))) > 0:
                            self.generator['name'] = 'ts'
                            break
                    except Exception:
                        continue

    @staticmethod
    def standardize_manifest_json(manifest):
        translators = []
        if 'translators' in manifest:
            for translator in manifest['translators']:
                if isinstance(translator, dict) and 'name' in translator:
                    translators.append(translator['name'])
                elif isinstance(translator, basestring):
                    translators.append(translator)
        manifest['translators'] = translators

        source_translations = []
        if 'source_translations' in manifest:
            if isinstance(manifest['source_translations'], dict):
                for key in manifest['source_translations'].keys():
                    source = manifest['source_translations'][key]
                    prod, lang, resource = key.split('-')
                    source['language_id'] = lang
                    source['resource_id'] = resource
                    source_translations.append(source)
                    if 'resource' not in manifest:
                        manifest['resource'] = {'id': resource, 'name': ""}
                    if 'format' not in manifest:
                        if resource == 'ulb' or resource == 'udb' or resource == 'bible':
                            manifest['format'] = 'usfm'
                        elif resource == 'obs':
                            manifest['format'] = 'markdown'
        manifest['source_translations'] = source_translations

        if 'sources' in manifest:
            manifest['source_translations'] = manifest['sources']
            del manifest['sources']

        if 'target_language' not in manifest:
            manifest['target_language'] = {'id': "", 'name': "", 'direction': "l2r"}
        if 'language' in manifest and isinstance(manifest['language'], dict):
            if 'lc' in manifest['language']:
                manifest['target_language']['id'] = manifest['language']['lc']
            elif 'slug' in manifest['language']:
                manifest['target_language']['id'] = manifest['language']['slug']

            if 'ln' in manifest['language']:
                manifest['target_language']['name'] = manifest['language']['ln']
            elif 'name' in manifest['language']:
                manifest['target_language']['name'] = manifest['language']['name']

            if 'direction' in manifest['language']:
                manifest['target_language']['direction'] = manifest['language']['direction']
            elif 'dir' in manifest['language']:
                manifest['target_language']['direction'] = manifest['language']['dir']
            del manifest['language']

        if 'project' not in manifest:
            manifest['project'] = {'id': "", 'name': ""}
            if 'project_id' in manifest:
                manifest['project']['id'] = manifest['project_id']
                if 'format' in manifest and manifest['format'] == 'usfm':
                    manifest['project']['name'] = BOOK_NAMES[manifest['project_id']]
                del manifest['project_id']
        elif 'slug' in manifest['project']:
            manifest['project']['id'] = manifest['project']['slug'].lower()
            manifest['project']['name'] = BOOK_NAMES[manifest['project']['slug'].lower()]
            del manifest['project']['slug']

        if 'project' in manifest and 'id' in manifest['project']:
            if manifest['project']['id'] in BOOK_NAMES:
                if 'resource' not in manifest or 'id' not in manifest['resource']:
                    manifest['resource'] = {
                        'id': 'bible',
                        'name': 'Bible'
                    }
                if 'format' not in manifest:
                    manifest['format'] = 'usfm'
            elif manifest['project']['id'] == 'obs':
                if 'resource' not in manifest or 'id' not in manifest['resource']:
                    manifest['resource'] = {
                        'id': 'obs',
                        'name': 'Open Bible Stories'
                    }
                if 'format' not in manifest:
                    manifest['format'] = 'markdown'
            else:
                if 'format' not in manifest:
                    manifest['format'] = 'markdown'

        if 'parent_drafts' not in manifest:
            manifest['parent_drafts'] = {}

        if 'finished_frames' in manifest:
            manifest['finished_chunks'] = manifest['finished_frames']
            del manifest['finished_frames']

        if 'type' not in manifest:
            manifest['type'] = {'id': 'text', 'name': 'Text'}

        if 'resource' not in manifest:
            manifest['resource'] = {'id': "", 'name': ""}
        elif 'id' in manifest['resource'] and manifest['resource']['id'] and ('name' not in manifest['resource'] or not manifest['resource']['name']):
            manifest['resource']['name'] = Manifest.get_resource_name(manifest['resource']['id'])
        if 'slug' in manifest:
            if not manifest['resource']['id']:
                manifest['resource']['id'] = manifest['slug']
            del manifest['slug']
        if 'name' in manifest:
            if not manifest['resource']['name']:
                manifest['resource']['name'] = manifest['name']
            del manifest['name']

        if manifest['format'] == 'usfm' and manifest['resource']['id'] not in ['ulb', 'udb', 'bible']:
            manifest['resource']['id'] = 'bible'
            if not manifest['resource']['name']:
                manifest['resource']['name'] = Manifest.get_resource_name(manifest['resource']['id'])

        manifest['package_version'] = Manifest.LATEST_VERSION

        return manifest
    
    @staticmethod
    def get_resource_name(resource_id):
        resource_id = resource_id.lower()
        if resource_id == 'ulb':
            return 'Unlocked Literal Bible'
        elif resource_id == 'udb':
            return 'Unlocked Dynamic Bible'
        elif resource_id == 'bible':
            return 'Bible'
        elif resource_id == 'obs':
            return 'Open Bible Stories'
        elif resource_id == 'tn':
            return 'translationNotes'
        elif resource_id == 'tw':
            return 'translationWords'
        elif resource_id == 'tq':
            return 'translationQuestions'
        elif resource_id == 'ta':
            return 'translationAcademy'
        return ''


class MetaData(object):
    def __init__(self, file_name=None):
        """
        Class constructor. Optionally accepts the name of a file to deserialize.
        :param str file_name: The name of a file to deserialize into a BibleMetaData object
        """
        # deserialize
        if file_name:
            if os.path.isfile(file_name):
                self.__dict__ = load_json_object(file_name)
                if 'versification' not in self.__dict__:
                    self.versification = 'ufw'
            else:
                raise IOError('The file {0} was not found.'.format(file_name))
        else:
            self.lang = ''
            self.name = ''
            self.slug = ''
            self.checking_entity = ''
            self.checking_level = '1'
            self.comments = ''
            self.contributors = ''
            self.publish_date = datetime.today().strftime('%Y-%m-%d')
            self.source_text = ''
            self.source_text_version = ''
            self.version = ''
            self.versification = 'ufw'
