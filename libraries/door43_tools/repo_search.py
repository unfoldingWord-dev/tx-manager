from __future__ import print_function, unicode_literals

import json
import logging
import time

import datetime

from libraries.models.manifest import TxManifest
from libraries.app.app import App


class RepoSearch(object):
    LANGUAGE_STATS_TABLE_NAME = 'language-stats'
    INVALID_URL_ERROR = 'repo not found for: '
    INVALID_LANG_URL_ERROR = 'language not found for: '
    DB_ACCESS_ERROR = 'could not access view counts for: '

    def __init__(self):
        """
        :param string language_stats_table_name:
        """
        self.logger = logging.getLogger('tx-manager')
        self.logger.addHandler(logging.NullHandler())
        self.error = None
        self.criterion = None

    def search_repos(self, criterion):
        """
        search for repos in manifest that match criterion
        :param criterion:
        :return:
        """
        self.logger.debug("Start: search_repos: " + json.dumps(criterion))

        self.criterion = json.loads(json.dumps(criterion))  # clone so we can modify

        try:
            tx_manager = App.db.query(TxManifest)
            selection = tx_manager

            for k in self.criterion:
                v = self.criterion[k]
                selection = self.appy_filter(selection, k, v)
                if selection is None:
                    return None
        except Exception as e:
            self.log_error('Failed to create a query: ' + str(e))
            return None

        results = selection.limit(20).all()  # get all matching
        if results:
            self.logger.debug('Returning stored view count of {0}')
        else:  # record is not present
            self.logger.debug('No entries found in manifest table')

        return results

    def appy_filter(self, selection, key, value):
        try:
            if key == "minViews":
                selection = selection.filter(TxManifest.views >= parse_int(value, 1))
            elif key == "daysForRecent":
                days = parse_int(value, 1)
                current = datetime.datetime.now()
                offset = -days * 24 * 60 * 60
                recent_in_seconds = current + datetime.timedelta(seconds=offset)
                selection = selection.filter(TxManifest.last_updated >= recent_in_seconds)
            elif (key == "repo_name") or (key == "user_name") or (key == "user_name") or (key == "manifest"):
                selection = set_contains_string_filter(selection, key, value)
            elif key == "resID":
                selection = selection.filter(TxManifest.resource_id.contains(value))
            elif key == "resType":
                selection = selection.filter(TxManifest.resource_type.contains(value))
            elif key == 'full_text':
                selection = selection.filter( (TxManifest.user_name.contains(value)) | (TxManifest.repo_name.contains(value))
                                  | (TxManifest.manifest.contains(value)))
            else:
                self.log_error('Unsupported filter (key,value): ({0},{1})'.format(key, value))
                return None

        except Exception as e:
            self.log_error('Failed to apply filter (key,value): ({0},{1}): '.format(key, value) + str(e))
            return None

        return selection


    def log_error(self, msg):
        self.error = msg
        self.logger.debug(msg)


def set_contains_string_filter(selection, key, value):
    db_key = getattr(TxManifest, key, None)
    selection = selection.filter(db_key.contains(value))
    return selection

def parse_int(s, default_value=None):
    try:
        return int(s)
    except ValueError:
        return default_value
