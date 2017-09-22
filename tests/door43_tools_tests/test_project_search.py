from __future__ import absolute_import, unicode_literals, print_function
import unittest
from datetime import datetime, timedelta
from libraries.app.app import App
from libraries.door43_tools.project_search import ProjectSearch
from libraries.models.manifest import TxManifest


class ProjectSearchTest(unittest.TestCase):

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        self.items = {}
        self.init_items()
        self.populate_table()

    def init_items(self):
        self.items = {
            'Door43/en_obs': {
                'repo_name': 'en_obs',
                'user_name': 'Door43',
                'lang_code': 'en',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 2,
                'last_updated': datetime.utcnow(),
                'manifest': {'description': 'Great Bible Stories'},
            },
            'JohnDoe/en_obs': {
                'repo_name': 'fr_obs',
                'user_name': 'JohnDoe',
                'lang_code': 'fr',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 3,
                'last_updated': self.get_time_n_months_back(11),
                'manifest': {'description': 'French Bible Stories'},
            },
            'francis/fr_ulb': {
                'repo_name': 'fr_ulb',
                'user_name': 'francis',
                'lang_code': 'fr',
                'resource_id': 'ulb',
                'resource_type': 'bundle',
                'title': 'Unlocked Literal Bible',
                'views': 12,
                'last_updated': self.get_time_n_months_back(6),
                'manifest': {'description': 'French Unlocked Literal Bible'},
            },
        }

    def populate_table(self):
        for idx in self.items:
            tx_manifest = TxManifest(**self.items[idx])
            tx_manifest.insert()

    def test_search_projects_for_en(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "languages": "[en]",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 1)
        self.assertEqual(search.url_params, '?lc=en')

    def test_search_projects_for_en2(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "languages": "en",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 1)
        self.assertEqual(search.url_params, '?lc=en')

    def test_search_projects_for_en_fr(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "languages": "[fr,en]",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 3)
        self.assertEqual(search.url_params, '?lc=en&lc=fr')

    def test_search_projects_for_en_fr_obs(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "languages": "[en,fr]",
            "full_text": "obs",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 2)
        self.assertEqual(search.url_params, '?lc=en&lc=fr&q=obs')

    def test_search_projects_for_obs(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "manifest": "obs",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 0)
        self.assertEqual(search.url_params, '?manifest=obs')

    def test_search_projects_for_res_obs(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "full_text": "fr",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 2)
        self.assertEqual(search.url_params, '?q=fr')

    def test_search_projects_for_en_fr_sort(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "sort_by": 'views',
            "languages": "[fr,en]",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 3)
        self.assertEqual(search.url_params, '?lc=en&lc=fr')
        last_count = -1
        for i in range(0, len(results)):
            item = results[i]
            count = item['views']
            self.assertGreaterEqual(count, last_count, msg="item {0} should be greater or equal to item {1}".format(i, i-1))
            last_count = count

    def test_search_projects_for_en_fr_sort_reverse(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "sort_by_reversed": 'views',
            "languages": "[fr,en]",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 3)
        self.assertEqual(search.url_params, '?lc=en&lc=fr')
        last_count = 9999999
        for i in range(0, len(results)):
            item = results[i]
            count = item['views']
            self.assertLessEqual(count, last_count, msg="item {0} should be less than or equal to item {1}".format(i, i-1))
            last_count = count

    def test_search_projects_for_fr(self):
        search = self.get_project_search()
        current_year = str(datetime.now().year)
        criterion = {
            "minViews": 1,
            "daysForRecent": 40,
            "resID": "obs",
            "time": current_year,
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 1)
        self.assertEqual(search.url_params, '?resID=obs&time=' + current_year)

    def test_search_projects_for_book(self):
        search = self.get_project_search()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "resType": "book",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 2)
        self.assertEqual(search.url_params, '?resType=book')

    def test_apply_filters(self):
        query = TxManifest.query()
        search = ProjectSearch()
        search.url_params = ""
        min_views_query = search.apply_filters(query, 'minViews', 10)
        self.assertEqual(min_views_query.count(), 1)  # count is the number of entries matched
        days_for_recent_query = search.apply_filters(query, 'daysForRecent', 30)
        self.assertEqual(days_for_recent_query.count(), 1)
        repo_query = search.apply_filters(query, 'repo_name', 'obs')
        self.assertEqual(repo_query.count(), 2)
        user_query = search.apply_filters(query, 'user_name', 'john')
        self.assertEqual(user_query.count(), 1)
        title_query = search.apply_filters(query, 'title', 'Open')
        self.assertEqual(title_query.count(), 2)
        full_text_query = search.apply_filters(query, 'full_text', '%great%')
        self.assertEqual(full_text_query.count(), 1)
        last_updated_query = search.apply_filters(query, 'time', str(datetime.utcnow().year))
        self.assertGreaterEqual(last_updated_query.count(), 1)
        resource_id_query = search.apply_filters(query, 'resID', 'obs')
        self.assertEqual(resource_id_query.count(), 2)
        resource_type_query = search.apply_filters(query, 'resType', 'bundle')
        self.assertEqual(resource_type_query.count(), 1)
        languages_query = search.apply_filters(query, 'languages', "[fr,es]")
        self.assertEqual(languages_query.count(), 2)

    #
    # helpers
    #

    def get_project_search(self):
        search = ProjectSearch()
        search.save_url_search = self.mock_save_url_search
        return search

    def mock_save_url_search(self):
        pass

    def get_time_n_months_back(self, months):
        current = datetime.now()
        offset = -months * 30 * 24 * 60 * 60  # in seconds
        recent_in_seconds = current + timedelta(seconds=offset)
        return recent_in_seconds
