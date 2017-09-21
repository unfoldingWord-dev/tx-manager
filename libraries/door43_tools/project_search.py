from __future__ import print_function, unicode_literals
import json
import datetime
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.models.manifest import TxManifest
from libraries.app.app import App


class ProjectSearch(object):
    INVALID_URL_ERROR = 'Project not found for: '
    INVALID_LANG_URL_ERROR = 'Language not found for: '
    DB_ACCESS_ERROR = 'Could not access view counts for: '

    def __init__(self):
        self.error = None
        self.criterion = None
        self.url_params = None

    def search_projects(self, criterion):
        """
        search for repos in manifest that match criterion
        :param criterion:
        :return:
        """
        App.logger.debug("Start: search_repos: " + json.dumps(criterion))

        self.criterion = json.loads(json.dumps(criterion))  # clone so we can modify

        try:
            query = TxManifest.query()

            self.url_params = ""
            k = 'languages'
            if k in self.criterion:  # apply languages first
                v = self.criterion[k]
                del self.criterion[k]
                query = self.apply_filters(query, k, v)
                if query is None:
                    return None

            for k in self.criterion:  # apply everything else
                v = self.criterion[k]
                query = self.apply_filters(query, k, v)
                if query is None:
                    return None

            if len(self.url_params) > 0 and (self.url_params[0] == '&'):
                self.url_params = self.url_params[1:]
            self.url_params = '?' + self.url_params

            if 'sort_by' in self.criterion:
                db_key = getattr(TxManifest, self.criterion['sort_by'], None)
                if db_key:
                    query = query.order_by(db_key)

            if 'sort_by_reversed' in self.criterion:
                db_key = getattr(TxManifest, self.criterion['sort_by_reversed'], None)
                if db_key:
                    query = query.order_by(db_key.desc())

        except Exception as e:
            self.log_error('Failed to create a query: ' + str(e))
            return None

        limit = 100 if 'matchLimit' not in self.criterion else self.criterion['matchLimit']
        results = query.limit(limit).all()  # get all matching
        data = []
        if results:
            App.logger.debug('Returning search result count of {0}'.format(len(results)))

            returned_fields = "repo_name, user_name, title, lang_code, manifest, last_updated, views" \
                if "returnedFields" not in self.criterion else self.criterion["returnedFields"]
            returned_fields = returned_fields.replace('resID', 'resource_id')
            returned_fields = returned_fields.replace('resType', 'resource_type')
            returned_fields = returned_fields.split(',')

            # copy wanted fields from this result item
            for result in results:
                item = {}
                for key in returned_fields:
                    key = key.strip()
                    if hasattr(result, key):
                        value = getattr(result, key)
                        destination_key = key
                        if key == 'resource_id':
                            destination_key = 'resID'
                        elif key == 'resource_type':
                            destination_key = 'resType'
                        item[destination_key] = value
                        if isinstance(value, datetime.datetime):
                            item[destination_key] = str(value)
                data.append(item)

        else:  # record is not present
            App.logger.debug('No entries found in search')

        App.db_close()

        self.save_url_search()
        return data

    def apply_filters(self, query, key, value):
        try:
            if key == "minViews":
                query = query.filter(TxManifest.views >= parse_int(value, 1))
            elif key == "daysForRecent":
                days = parse_int(value, 1)
                current = datetime.datetime.now()
                offset = -days * 24 * 60 * 60  # in seconds
                recent_in_seconds = current + datetime.timedelta(seconds=offset)
                query = query.filter(TxManifest.last_updated >= recent_in_seconds)
            elif key == 'repo_name':
                query = query.filter(TxManifest.repo_name.contains(value))
                self.url_params += '&' + key + '=' + value
            elif key == 'user_name':
                query = query.filter(TxManifest.user_name.contains(value))
                self.url_params += '&' + key + '=' + value
            elif key == 'title':
                query = query.filter(TxManifest.title.contains(value))
                self.url_params += '&' + key + '=' + value
            elif key == 'manifest':
                query = query.filter(TxManifest.manifest.contains(value))
                self.url_params += '&' + key + '=' + value
            elif key == "time":
                query = query.filter(TxManifest.last_updated.contains(value))
                self.url_params += '&' + key + '=' + value
            elif key == "resID":
                query = query.filter(TxManifest.resource_id.contains(value))
                self.url_params += '&' + key + '=' + value
            elif key == "resType":
                query = query.filter(TxManifest.resource_type.contains(value))
                self.url_params += '&' + key + '=' + value
            elif key == "languages":
                query, filter_set = set_contains_set_filter(query, "lang_code", value)
                if filter_set is None:
                    self.url_params += '&lc=' + value
                else:
                    filter_set.sort()
                    for filter in filter_set:
                        self.url_params += '&lc=' + filter
            elif key == 'full_text':
                query = query.filter((TxManifest.user_name.contains(value))
                                     | (TxManifest.repo_name.contains(value))
                                     | (TxManifest.manifest.contains(value)))
                self.url_params += '&' + 'q' + '=' + value
            elif key == "returnedFields" or key == "sort_by" or key == "sort_by_reversed" or key == "matchLimit":
                pass  # skip this item
            else:
                pass  # Allow unsupported fields to be ignored

        except Exception as e:
            self.log_error('Failed to apply filter (key,value): ({0},{1}): '.format(key, value) + str(e))
            return None

        return query

    def log_error(self, msg):
        self.error = msg
        App.logger.debug(msg)

    def save_url_search(self):
        PageMetrics().increment_search_params(self.url_params)


def set_contains_set_filter(query, key, value):
    db_key = getattr(TxManifest, key, None)
    if value[:1] == '[':
        filter_set_str = value[1:].split(']')
        filter_set = filter_set_str[0].split(',')
        query = query.filter(db_key.in_(filter_set))
        return query, filter_set

    query = query.filter(db_key.like(value))
    return query, None


def parse_int(s, default_value=None):
    try:
        return int(s)
    except ValueError:
        return default_value
