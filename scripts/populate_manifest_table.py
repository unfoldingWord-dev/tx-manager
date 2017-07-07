#!/usr/bin/env python
"""
Makes sure every project is in the manifest table based on what is in the cdn.door43.org/u bucket. If it is already in
the table, it doesn't do anything

"""
from __future__ import unicode_literals, print_function
import os
import boto3
import logging
import sys
import yaml
import json
import tempfile
import pickle
from datetime import datetime


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

already_in_db = {}

keys_file = None 
already_in_db_file = None

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
    'reg': {
        'title': 'Regular',
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
    'obs-tn': {
        'title': 'Open Bible Stories translationNotes',
        'type': 'help',
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


def save_obj(obj, fname):
    with open(fname, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(fname):
    with open(fname, 'rb') as f:
        return pickle.load(f)


def get_build_logs(bucket):
    build_logs = []
    objects = bucket.objects.filter(Prefix='u/')
    for obj in objects:
        if obj.key.endswith('/build_log.json'):
            build_logs.append(obj.key)
    return build_logs


def add_to_manifest(resource, bucket_name, table_name, key):
    parts = key.split('/')
    if len(parts) != 5:
        return
    repo_name = parts[2]
    user_name = parts[1]
    commit = parts[3]

    logger.info('Processing {0}...'.format(key))

    build_log = json.loads(resource.Object(bucket_name=bucket_name, key=key).get()['Body'].read())
    if 'build_logs' in build_log:
        build_log = build_log['build_logs'][0]

    in_db_key = '{0}/{1}'.format(repo_name, user_name)
    if 'created_at' not in build_log or (in_db_key in already_in_db and
                                                 already_in_db[in_db_key] > build_log['created_at']):
        return

    dbtable = boto3.resource('dynamodb').Table(table_name)

    manifest = None
    try:
        manifest = yaml.load(resource.Object(bucket_name=bucket_name, key='u/{0}/{1}/{2}/manifest.yaml'.format(user_name, repo_name, commit)).get()['Body'].read())
    except:
        pass

    if not manifest:
        try:
            manifest = json.loads(resource.Object(bucket_name=bucket_name, key='u/{0}/{1}/{2}/manifest.json'.format(user_name, repo_name, commit)).get()['Body'].read())
        except:
            pass

    if manifest and 'dublin_core' in manifest:
        data = {
            'repo_name_lower': repo_name.lower(),
            'user_name_lower': user_name.lower(),
            'repo_name': repo_name,
            'user_name': user_name,
            'lang_code': manifest['dublin_core']['language']['identifier'].lower(),
            'resource_id': manifest['dublin_core']['identifier'].lower(),
            'resource_type': manifest['dublin_core']['type'].lower(),
            'title': manifest['dublin_core']['title'],
            'views': 0,
            'last_updated': build_log['created_at'],
            'manifest': json.dumps(manifest),
            'manifest_lower':json.dumps(manifest).lower(),
        }
    else:
        parts = repo_name.split('_')
        if len(parts) == 1:
            parts = repo_name.split('-')
        type = build_log['resource_type']
        if type in resource_map:
            resource = resource_map[type]
        else:
            resource = {
                'title': repo_name,
                'type': 'book',
                'format': 'text/md'
            }
        if not type:
            if manifest and 'resource' in manifest and 'id' in manifest['resource'] and manifest['resource']['id']:
                type = manifest['resource']['id']
                resource['title'] = manifest['resource']['name']
            else:
                type = repo_name
        if manifest and 'target_language' in manifest and 'id' in manifest['target_language'] and manifest['target_language']['id']:
            lang = manifest['target_language']['id']
            if 'direction' in manifest['target_language']:
                direction = manifest['target_language']['direction']
            else:
                direction = 'ltr'
            lang_title = manifest['target_language']['name']
        else:
            if len(parts) > 1 and parts[0] == 'uw':
                lang = parts[-1]
            else:
                lang = parts[0]
            direction = 'ltr'
            lang_title = lang
        data = {
            'repo_name_lower': repo_name.lower(),
            'user_name_lower': user_name.lower(),
            'repo_name': repo_name,
            'user_name': user_name,
            'lang_code': lang,
            'resource_id': type,
            'resource_type': resource['type'],
            'title': resource['title'],
            'views': 0,
            'last_updated': build_log['created_at'] 
        }
        data['manifest'] = json.dumps({
            'checking': {'checking_entity': ['Wycliffe Associates'], 'checking_level': '1'},
            'dublin_core': {
                'conformsto': 'rc0.2',
                'contributor': ['unfoldingWord', 'Wycliffe Associates'],
                'creator': 'Wycliffe Associates',
                'description': '',
                'format': resource['format'],
                'issued': datetime.utcnow().strftime('%Y-%m-%d'),
                'modified': datetime.utcnow().strftime('%Y-%m-%d'),
                'identifier': data['resource_id'],
                'language': {'identifier': data['lang_code'], 'direction': direction, 'title': lang_title},
                'type': data['resource_type'],
                'title': data['title']
            },
            'projects': [{
                'sort': '1',
                'identifier': data['resource_id'],
                'title': data['title'],
                'path': './',
                'versification': '',
                'categories': []
            }]
        })
        data['manifest_lower'] = data['manifest'].lower()
    dbtable.put_item(Item=data)
    already_in_db[in_db_key] = build_log['created_at'] 
    save_obj(already_in_db, already_in_db_file)


def main():
    global keys_file, already_in_db_file
    if len(sys.argv) < 3:
        logger.critical('You must provide a bucket name and table name.')
        logger.critical('Example: ./populate_manifest_table.py cdn.door43.org tx-manifest')
        exit(1)
    bucket_name = sys.argv[1]
    table_name = sys.argv[2]
    resource = boto3.resource('s3')
    bucket = resource.Bucket(bucket_name)
    keys_file = os.path.join(tempfile.gettempdir(), 'populate_manifest_table_{0}_keys.txt'.format(bucket_name)) 
    already_in_db_file = os.path.join(tempfile.gettempdir(), 'populate_manifest_table_{0}.txt'.format(table_name)) 
    if os.path.isfile(keys_file):
        keys = load_obj(keys_file)
    else:
        keys = get_build_logs(bucket)
        save_obj(keys, keys_file)
    if os.path.isfile(already_in_db_file):
        already_in_db = load_obj(already_in_db_file)
    for k in keys:
        add_to_manifest(resource, bucket_name, table_name, k)


if __name__ == '__main__':
    main()
