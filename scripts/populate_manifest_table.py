#!/usr/bin/env python
"""
Makes sure every project is in the manifest table based on what is in the cdn.door43.org/u bucket. If it is already in
the table, it doesn't do anything

"""
import boto3
import logging
import sys
import yaml
import json
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

    in_db_key = '{0}/{1}'.format(repo_name, user_name)
    if in_db_key in already_in_db:
        return

    logger.info('Processing {0}...'.format(key))

    dbtable = boto3.resource('dynamodb').Table(table_name)

    response = dbtable.get_item(
        Key={'repo_name': repo_name, 'user_name': user_name}
    )
    if 'Item' in response:
        already_in_db[in_db_key] = True
        return

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
            'repo_name': repo_name,
            'user_name': user_name,
            'lang_code': manifest['dublin_core']['language']['identifier'],
            'resource_id': manifest['dublin_core']['identifier'],
            'resource_type': manifest['dublin_core']['type'],
            'title': manifest['dublin_core']['title'],
            'views': 0,
            'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'manifest': json.dumps(manifest)
        }
    else:
        build_log = json.loads(resource.Object(bucket_name=bucket_name, key=key).get()['Body'].read())
        if 'build_logs' in build_log:
            build_log = build_log['build_logs'][0]
        parts = repo_name.split('_')
        if len(parts) == 1:
            parts = repo_name.split('-')
        type = build_log['resource_type']
        data = {
            'repo_name': repo_name,
            'user_name': user_name,
            'lang_code': parts[0],
            'resource_id': type,
            'resource_type': resource_map[type]['type'],
            'title': resource_map[type]['title'],
            'views': 0,
            'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        data['manifest'] = json.dumps({
            'checking': {'checking_entity': ['Wycliffe Associates'], 'checking_level': '1'},
            'dublin_core': {
                'conformsto': 'rc0.2',
                'contributor': ['unfoldingWord', 'Wycliffe Associates'],
                'creator': 'Wycliffe Associates',
                'description': '',
                'format': resource_map[type]['format'],
                'issued': datetime.utcnow().strftime('%Y-%m-%d'),
                'modified': datetime.utcnow().strftime('%Y-%m-%d'),
                'identifier': data['resource_id'],
                'language': {'identifier': data['lang_code']},
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
    dbtable.put_item(Item=data)
    already_in_db[in_db_key] = True


def main():
    if len(sys.argv) < 3:
        logger.critical('You must provide a bucket name and table name.')
        logger.critical('Example: ./populate_manifest_table.py cdn.door43.org tx-manifest')
        exit(1)
    bucket_name = sys.argv[1]
    table_name = sys.argv[2]
    resource = boto3.resource('s3')
    bucket = resource.Bucket(bucket_name)
    keys = get_build_logs(bucket)
    for k in keys:
        add_to_manifest(resource, bucket_name, table_name, k)


if __name__ == '__main__':
    main()
