#!/usr/bin/env python
"""
Adds N number of rows of dummy data to the manifest table specified

"""
from __future__ import unicode_literals, print_function
import random
import boto3
import logging
import sys
import json
import time
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

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


def strTimeProp(start, end, format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def randomDate(start, end, prop):
    return strTimeProp(start, end, '%Y-%m-%dT%H:%M:%SZ', prop)



def add_dummy_data_to_manifest_table(table_name, new_rows, start):
    manifest_table = boto3.resource('dynamodb').Table(table_name)

    for i in range(start, start+new_rows):
        print("Adding row {0} of {1}".format(i, start+new_rows-1))
        repo_name_lower = 'repo{0}'.format(i)
        user_name_lower = 'user{0}'.format(i)

        type = resource_map.keys()[random.randint(1, len(resource_map.keys()))-1]
        resource = resource_map[type]

        last_updated = randomDate("2015-01-01T00:00:00Z", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), random.random())
        data = {
            'repo_name_lower': repo_name_lower,
            'user_name_lower': user_name_lower,
            'repo_name': repo_name_lower,
            'user_name': user_name_lower,
            'lang_code': 'en',
            'resource_id': type,
            'resource_type': resource['type'],
            'title': resource['title'],
            'views': random.randint(0, 500),
            'last_updated': last_updated
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
                'language': {'identifier': data['lang_code'], 'direction': 'ltr', 'title': 'English'},
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
        data['manifest_lower'] = data['manifest'].lower();
        manifest_table.put_item(Item=data)


def main():
    if len(sys.argv) < 3:
        logger.critical('You must provide a table name and how many dummy rows to add.')
        logger.critical('Example: ./add_dummy_data_to_manifest_table.py tx-manifest 5000')
        exit(1)
    table_name = sys.argv[1]
    new_rows = int(sys.argv[2])
    start = 1
    if len(sys.argv) > 3:
        start = int(sys.argv[3])
    add_dummy_data_to_manifest_table(table_name, new_rows, start)


if __name__ == '__main__':
    main()
