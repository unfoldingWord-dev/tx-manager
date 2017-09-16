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
                'manifest': '',
            },
            'JohnDoe/en_obs': {
                'repo_name': 'fr_obs',
                'user_name': 'JohnDoe',
                'lang_code': 'fr',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 1,
                'last_updated': self.get_time_n_months_back(11),
                'manifest': '',
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
                'manifest': '',
            },
        }

    def populate_table(self):
        for idx in self.items:
            tx_manifest = TxManifest(**self.items[idx])
            App.db().add(tx_manifest)
        App.db().commit()
        App.db_close()

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
