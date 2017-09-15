from __future__ import absolute_import, unicode_literals, print_function
import unittest
from datetime import datetime
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
                'views': 2,
                'last_updated': datetime.strptime('2016-12-21T05:23:01Z', '%Y-%m-%dT%H:%M:%SZ'),
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
                'last_updated': datetime.strptime('2017-02-11T15:43:11Z', '%Y-%m-%dT%H:%M:%SZ'),
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
        search = ProjectSearch()
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

    def test_search_projects_for_en_fr(self):
        search = ProjectSearch()
        criterion = {
            "minViews": 1,
            "daysForRecent": 365,
            "languages": "[en,fr]",
            "returnedFields": "repo_name, user_name, title, lang_code, last_updated, views"
        }
        results = search.search_projects(criterion)
        self.assertIsNone(search.error)
        self.assertEqual(len(results), 3)
        self.assertEqual(search.url_params, '?lc=en&lc=fr')

    def test_search_projects_for_en_fr_obs(self):
        search = ProjectSearch()
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
        search = ProjectSearch()
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
        search = ProjectSearch()
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
