from __future__ import print_function, unicode_literals
import logging
import os
import tempfile
import urlparse

from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.models.manifest import TxManifest


class ViewCount(object):
    MANIFEST_TABLE_NAME = 'tx-manifest'

    def __init__(self, gogs_user_token=None, manifest_table_name=None):
        """
        :param string gogs_user_token:
        :param string manifest_table_name:
        """
        self.manifest_table_name = manifest_table_name
        self.logger = logging.getLogger()

        # move everything down one directory levek for simple delete
        self.intermediate_dir = 'tx-manager'
        self.base_temp_dir = os.path.join(tempfile.gettempdir(), self.intermediate_dir)

    def get_view_count(self, path, increment=0):
        self.logger.debug("Start: generateDashboard")

        response = {
            'title': 'View Count',
            'ErrorMessage': 'repo not found for: ' + path
        }

        parsed = urlparse.urlparse(path)
        try:
            u, repo_owner, repo_name = parsed.path.split('/')[0:3]
        except:
            self.logger.warning("Invalid repo url: " + path)
            return response

        if u != 'u':
            self.logger.warning("Invalid repo url: " + path)
            return response

        site = ''
        netloc_parts = parsed.netloc.split('-')
        if len(netloc_parts) > 1:
            site = netloc_parts[0]
        self.manifest_table_name = site + ViewCount.MANIFEST_TABLE_NAME
        self.manifest_db_handler = DynamoDBHandler(self.manifest_table_name)

        self.logger.debug("Valid repo url: " + path)
        try:
            tx_manifest = TxManifest(db_handler=self.manifest_db_handler)
            # First see if manifest already exists in DB and update it if it is
            tx_manifest.repo_name = repo_name
            tx_manifest.user_name = repo_owner
            tx_manifest.load()
            if tx_manifest.repo_name:
                if increment:
                    tx_manifest.views += 1
                    self.logger.debug('Incrementing view count to {0}'.format(tx_manifest.views))
                    tx_manifest.update()
            else:
                self.logger.debug('Inserting manifest into manifest table')
                tx_manifest.views = 0
                if increment:
                    tx_manifest.views += 1
                manifest_data = {
                    'repo_name': repo_name,
                    'user_name': repo_owner,
                    'lang_code': '',
                    'resource_id': '',
                    'resource_type': '',
                    'title': '',
                    'last_updated': None,
                    'manifest': '',
                    'views': tx_manifest.views
                }
                tx_manifest.populate(manifest_data)
                tx_manifest.insert()

            response['view_count'] = tx_manifest.views
        except:
            response['ErrorMessage'] = 'could not access view counts for: ' + path
            pass

        del response['ErrorMessage']
        return response

