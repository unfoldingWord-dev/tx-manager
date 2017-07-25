from __future__ import print_function, unicode_literals
import logging
import urlparse
from decimal import Decimal
from datetime import datetime
from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
from libraries.models.language_stats import LanguageStats
from libraries.models.manifest import TxManifest


class PageMetrics(object):
    MANIFEST_TABLE_NAME = 'tx-manifest'
    LANGUAGE_STATS_TABLE_NAME = 'language-stats'
    INVALID_URL_ERROR = 'repo not found for: '
    DB_ACCESS_ERROR = 'could not access view counts for: '

    def __init__(self, manifest_table_name=None, language_stats_table_name=None):
        """
        :param string language_stats_table_name:
        :param string manifest_table_name:
        """
        self.manifest_table_name = manifest_table_name
        self.manifest_db_handler = None
        self.language_stats_table_name = language_stats_table_name
        self.language_stats_db_handler = None
        self.logger = logging.getLogger()

    def get_view_count(self, path, increment=0):
        self.logger.debug("Start: get_view_count")

        response = {  # default to error
            'ErrorMessage': PageMetrics.INVALID_URL_ERROR + path
        }

        parsed = urlparse.urlparse(path)
        try:
            empty, u, repo_owner, repo_name = parsed.path.split('/')[0:4]
        except:
            self.logger.warning("Invalid repo url: " + path)
            return response

        if (empty != '') or (u != 'u'):
            self.logger.warning("Invalid repo url: " + path)
            return response

        del response['ErrorMessage']
        if not self.manifest_db_handler:
            self.init_manifest_table(parsed)

        self.logger.debug("Valid repo url: " + path)
        try:
            # First see record already exists in DB
            tx_manifest = TxManifest({'repo_name_lower': repo_name.lower(), 'user_name_lower': repo_owner.lower()},
                                     db_handler=self.manifest_db_handler)
            if tx_manifest.repo_name:
                if increment:
                    tx_manifest.views += 1
                    self.logger.debug('Incrementing view count to {0}'.format(tx_manifest.views))
                    tx_manifest.update()
                else:
                    self.logger.debug('Returning stored view count of {0}'.format(tx_manifest.views))
            else:  # record is not present
                tx_manifest.views = 0
                self.logger.debug('No entries for page in manifest table')

            view_count = tx_manifest.views
            if type(view_count) is Decimal:
                view_count = int(view_count.to_integral_value())
            response['view_count'] = view_count

        except Exception as e:
            self.logger.exception('Error accessing manifest', exc_info=e)
            response['ErrorMessage'] = PageMetrics.DB_ACCESS_ERROR + path
            return response

        return response

    def get_language_count(self, path, increment=0):
        self.logger.debug("Start: get_language_count")

        response = {  # default to error
            'ErrorMessage': PageMetrics.INVALID_URL_ERROR + path
        }

        parsed = urlparse.urlparse(path)
        try:
            parts = parsed.path.split('/')
            if len(parts) == 2:
                empty, language_code = parts
            else:
                empty, language_code, page = parts
        except:
            self.logger.warning("Invalid language page url: " + path)
            return response

        if (empty != '') or (len(parts) > 3) or (not language_code) or (len(language_code) < 2):
            self.logger.warning("Invalid language page url: " + path)
            return response

        del response['ErrorMessage']
        if not self.language_stats_db_handler:
            self.init_language_stats_table(parsed)

        self.logger.debug("Valid '" + language_code + "' url: " + path)
        try:
            # First see record already exists in DB
            lang_stats = LanguageStats({'lang_code': language_code},
                                       db_handler=self.language_stats_db_handler)
            if lang_stats.lang_code:  # see if data in table
                if increment:
                    lang_stats.views += 1
                    self.logger.debug('Incrementing view count to {0}'.format(lang_stats.views))
                    self.updateLangStats(lang_stats)
                else:
                    self.logger.debug('Returning stored view count of {0}'.format(lang_stats.views))

            else:  # record is not present
                lang_stats.views = 0
                if increment:
                    lang_stats.lang_code = language_code
                    lang_stats.views += 1
                    self.logger.debug('No entries for {0} in {1} table, creating'.format(language_code,
                                                                                    self.language_stats_table_name))
                    self.updateLangStats(lang_stats)
                else:
                    self.logger.debug('No entries for {0} in {1} table'.format(language_code,
                                                                                     self.language_stats_table_name))

            view_count = lang_stats.views
            if type(view_count) is Decimal:
                view_count = int(view_count.to_integral_value())
            response['view_count'] = view_count

        except Exception as e:
            self.logger.exception('Error accessing {0} table'.format(self.language_stats_table_name), exc_info=e)
            response['ErrorMessage'] = PageMetrics.DB_ACCESS_ERROR + path
            return response

        return response

    def updateLangStats(self, lang_stats):
        """
        update the entry in the database
        :param lang_stats:
        :return:
        """
        utcnow = datetime.utcnow()
        lang_stats.last_updated = utcnow.strftime("%Y-%m-%dT%H:%M:%SZ")
        lang_stats.update()

    def init_language_stats_table(self, parsed):
        if not self.language_stats_table_name:
            site = ''
            netloc_parts = parsed.netloc.split('-')
            if len(netloc_parts) > 1:
                site = netloc_parts[0]
            self.language_stats_table_name = site + '-' + PageMetrics.LANGUAGE_STATS_TABLE_NAME
        self.language_stats_db_handler = DynamoDBHandler(self.language_stats_table_name)

    def init_manifest_table(self, parsed):
        if not self.manifest_table_name:
            site = ''
            netloc_parts = parsed.netloc.split('-')
            if len(netloc_parts) > 1:
                site = netloc_parts[0]
            self.manifest_table_name = site + '-' + PageMetrics.MANIFEST_TABLE_NAME
        self.manifest_db_handler = DynamoDBHandler(self.manifest_table_name)
