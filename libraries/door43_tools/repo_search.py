from __future__ import print_function, unicode_literals

import json
import logging
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

    def search_repos(self, criterion):
        """
        get normal user page view count with optional increment
        :param path:
        :param increment:
        :return:
        """
        self.logger.debug("Start: search_repos: " + json.dumps(criterion))

        tx_manifest = App.db.query(TxManifest).filter(TxManifest.views > 0).filter(TxManifest.repo_name.contains("en")).limit(20)
            # .limit(20)
        results = tx_manifest.all()
        if results:
            self.logger.debug('Returning stored view count of {0}')
        else:  # record is not present
            self.logger.debug('No entries for page in manifest table')
            view_count = 0

        return view_count
