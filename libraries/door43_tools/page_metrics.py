from __future__ import print_function, unicode_literals
import re
import urlparse
from decimal import Decimal
from datetime import datetime
from operator import itemgetter
from boto3.dynamodb.conditions import Key
from libraries.models.language_stats import LanguageStats
from libraries.models.manifest import TxManifest
from libraries.app.app import App


class PageMetrics(object):
    INVALID_URL_ERROR = 'repo not found for: '
    INVALID_LANG_URL_ERROR = 'language not found for: '
    DB_ACCESS_ERROR = 'could not access view counts for: '

    def __init__(self):
        self.languages = None
        self.searches = None

    def get_view_count(self, path, increment=0):
        """
        get normal user page view count with optional increment
        :param path:
        :param increment:
        :return:
        """
        App.logger.debug("Start: get_view_count")

        response = {  # default to error
            'ErrorMessage': PageMetrics.INVALID_URL_ERROR + path
        }

        parsed = urlparse.urlparse(path)
        try:
            empty, u, repo_owner, repo_name = parsed.path.split('/')[0:4]
        except:
            App.logger.warning("Invalid repo url: " + path)
            return response

        if (empty != '') or (u != 'u'):
            App.logger.warning("Invalid repo url: " + path)
            return response

        del response['ErrorMessage']

        App.logger.debug("Valid repo url: " + path)
        # First see record already exists in DB
        tx_manifest = App.db().query(TxManifest).filter_by(repo_name=repo_name, user_name=repo_owner).first()
        if tx_manifest:
            if increment:
                tx_manifest.views += 1
                App.logger.debug('Incrementing view count to {0}'.format(tx_manifest.views))
                App.db().commit()
            else:
                App.logger.debug('Returning stored view count of {0}'.format(tx_manifest.views))
            view_count = tx_manifest.views
        else:  # record is not present
            App.logger.debug('No entries for page in manifest table')
            view_count = 0
        response['view_count'] = view_count
        App.db_close()
        return response

    def get_language_view_count(self, path, increment=0):
        """
        get language page view count with optional increment
        :param path:
        :param increment:
        :return:
        """
        App.logger.debug("Start: get_language_count")

        response = {  # default to error
            'ErrorMessage': PageMetrics.INVALID_LANG_URL_ERROR + path
        }

        parsed = urlparse.urlparse(path)
        try:
            parts = parsed.path.split('/')
            if len(parts) == 2:
                empty, language_code = parts
            else:
                empty, language_code, page = parts
        except:
            App.logger.warning("Invalid language page url: " + path)
            return response

        language_code = self.validate_language_code(language_code)
        if not language_code:
            App.logger.warning("Invalid language page url: " + path)
            return response

        del response['ErrorMessage']
        language_code = language_code.lower()

        App.logger.debug("Valid '" + language_code + "' url: " + path)
        try:
            # First see record already exists in DB
            lang_stats = LanguageStats({'lang_code': language_code})
            if lang_stats.lang_code:  # see if data in table
                if increment:
                    lang_stats.views += 1
                    App.logger.debug('Incrementing view count to {0}'.format(lang_stats.views))
                    self.update_lang_stats(lang_stats)
                else:
                    App.logger.debug('Returning stored view count of {0}'.format(lang_stats.views))

            else:  # record is not present
                lang_stats.views = 0
                if increment:
                    lang_stats.lang_code = language_code
                    lang_stats.views += 1
                    App.logger.debug('No entries for {0} in {1} table, creating'.format(language_code,
                                                                                        App.language_stats_table_name))
                    self.update_lang_stats(lang_stats)
                else:
                    App.logger.debug('No entries for {0} in {1} table'.format(language_code,
                                                                              App.language_stats_table_name))

            view_count = lang_stats.views
            if type(view_count) is Decimal:
                view_count = int(view_count.to_integral_value())
            response['view_count'] = view_count

        except Exception as e:
            App.logger.exception('Error accessing {0} table'.format(App.language_stats_table_name), exc_info=e)
            response['ErrorMessage'] = PageMetrics.DB_ACCESS_ERROR + path
            return response

        return response

    def increment_search_params(self, path):
        """
        increment search parameter count
        :param path:
        :return:
        """
        parts = path.split('?')
        if (len(parts) > 1) and (len(parts[1]) > 0):
            search_params = '?' + parts[1]
        else:
            App.logger.warning("Invalid language page url: '{0}'".format(path))
            return -1

        App.logger.debug("Valid search params '" + search_params + "' from url: " + path)
        try:
            # First see record already exists in DB
            lang_stats = LanguageStats({'lang_code': search_params})
            if lang_stats.lang_code:  # see if data in table
                lang_stats.views += 1
                lang_stats.search_type = 'Y'
                App.logger.debug('Incrementing view count to {0}'.format(lang_stats.views))
                self.update_lang_stats(lang_stats)

            else:  # record is not present, creat
                lang_stats.views = 0
                lang_stats.lang_code = search_params
                lang_stats.views += 1
                lang_stats.search_type = 'Y'
                App.logger.debug('No entries for {0} in {1} table, creating'.format(search_params,
                                                                                    App.language_stats_table_name))
                self.update_lang_stats(lang_stats)

            view_count = lang_stats.views
            if type(view_count) is Decimal:
                view_count = int(view_count.to_integral_value())

        except Exception as e:
            App.logger.exception('Error accessing {0} table'.format(App.language_stats_table_name), exc_info=e)
            return -1

        return view_count

    @staticmethod
    def validate_language_code(language_code):
        """
        verifies that language_code is valid format and returns the language code if it's valid, else returns None
        :param language_code:
        :return:
        """
        language_code = language_code.lower()
        lang_code_pattern = re.compile("^[a-z]{2,3}(-[a-z0-9]{2,4})?$")  # e.g. ab, abc, pt-br, es-419, sr-latn
        valid_lang_code = lang_code_pattern.match(language_code)
        if not valid_lang_code:
            extended_lang_code_pattern = re.compile("^[a-z]{2,3}(-x-[\w\d]+)?$", re.UNICODE)  # e.g. abc-x-abcdefg
            valid_lang_code = extended_lang_code_pattern.match(language_code)
            if not valid_lang_code:
                extended_lang_code_pattern2 = re.compile("^(-x-[\w\d]+)$", re.UNICODE)  # e.g. -x-abcdefg
                valid_lang_code = extended_lang_code_pattern2.match(language_code)
                if not valid_lang_code:
                    language_code = None
        return language_code

    @staticmethod
    def update_lang_stats(lang_stats):
        """
        update the entry in the database
        :param lang_stats:
        :return:
        """
        utcnow = datetime.utcnow()
        lang_stats.last_updated = utcnow.strftime("%Y-%m-%dT%H:%M:%SZ")
        lang_stats.update()

    def list_language_views(self, reverse_sort=True, max_count=0):
        """
        get list of all the language view records
        :return:
        """
        self.languages = self.list_language_table_entries(reverse_sort=reverse_sort, max_count=max_count,
                                                          search_type=False)
        return self.languages

    def list_search_views(self, reverse_sort=True, max_count=0):
        """
        get list of all the search records
        :return:
        """
        self.searches = self.list_language_table_entries(reverse_sort=reverse_sort, max_count=max_count,
                                                         search_type=True)
        return self.searches

    def list_language_table_entries(self, reverse_sort=True, max_count=20, search_type=False):
        """
        get list of all the language table records filtered by type
        :return:
        """
        search_key = 'N' if search_type is False else 'Y'
        params = {
            'IndexName': 'search_type-views-index',
            'KeyConditionExpression': Key('search_type').eq(search_key),
            'ScanIndexForward': not reverse_sort
        }
        if max_count > 0:
            params['Limit'] = max_count
        db_handler = App.language_stats_db_handler()
        results = db_handler.query_raw(**params)
        items = results['Items']
        return items

    def get_language_views_sorted_by_count(self, reverse_sort=True, max_count=0):
        """
        Get list of language views records sorted by views.
        :param max_count:
        :param reverse_sort:
        :return:
        """
        newlist = None
        if self.languages is None:
            try:
                self.list_language_views(reverse_sort=reverse_sort, max_count=max_count)
            except:
                pass

        if self.languages is not None:
            newlist = sorted(self.languages, key=itemgetter('views'), reverse=reverse_sort)

        return newlist

    def get_searches_sorted_by_count(self, reverse_sort=True, max_count=0):
        """
        Get list of language views records sorted by views.
        :param max_count:
        :param reverse_sort:
        :return:
        """
        newlist = None
        if self.searches is None:
            try:
                self.list_search_views(reverse_sort=reverse_sort, max_count=max_count)
            except:
                pass

        if self.searches is not None:
            newlist = sorted(self.searches, key=itemgetter('views'), reverse=reverse_sort)

        return newlist
