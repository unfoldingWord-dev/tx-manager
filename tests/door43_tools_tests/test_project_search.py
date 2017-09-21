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
                'last_updated': datetime.utcnow() - timedelta(days=366),
                'manifest': {'description': 'Great Bible Stories'},
            },
            'JohnDoe/en_obs': {
                'repo_name': 'en_obs',
                'user_name': 'JohnDoe',
                'lang_code': 'en',
                'resource_id': 'obs',
                'resource_type': 'book',
                'title': 'Open Bible Stories',
                'views': 3,
                'last_updated': datetime.utcnow() - timedelta(weeks=4),
                'manifest': {'description': 'English Bible Stories'},
            },
            'francis/fr_ulb': {
                'repo_name': 'fr_ulb',
                'user_name': 'francis',
                'lang_code': 'fr',
                'resource_id': 'ulb',
                'resource_type': 'bundle',
                'title': 'Unlocked Literal Bible',
                'views': 12,
                'last_updated': datetime.utcnow() - timedelta(days=3),
                'manifest': {'description': 'French Bible Stories'},
            },
        }

    def populate_table(self):
        for idx in self.items:
            tx_manifest = TxManifest(**self.items[idx])
            tx_manifest.insert()

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
        self.assertEqual(len(results), 2)

    def test_apply_filters(self):
        query = TxManifest.query()
        search = ProjectSearch()
        min_views_query = search.apply_filters(query, 'minViews', 10)
        self.assertEqual(min_views_query.count(), 1)
        days_for_recent_query = search.apply_filters(query, 'daysForRecent', 30)
        self.assertEqual(days_for_recent_query.count(), 2)
        repo_query = search.apply_filters(query, 'repo_name', 'obs')
        self.assertEqual(repo_query.count(), 2)
        user_query = search.apply_filters(query, 'user_name', 'john')
        self.assertEqual(user_query.count(), 1)
        title_query = search.apply_filters(query, 'title', 'Open')
        self.assertEqual(title_query.count(), 2)
        full_text_query = search.apply_filters(query, 'full_text', '%great%')
        self.assertEqual(full_text_query.count(), 1)
        last_updated_query = search.apply_filters(query, 'time', '2016')
        self.assertEqual(last_updated_query.count(), 1)
        resource_id_query = search.apply_filters(query, 'resID', 'obs')
        self.assertEqual(resource_id_query.count(), 2)
        resource_type_query = search.apply_filters(query, 'resType', 'bundle')
        self.assertEqual(resource_type_query.count(), 1)
        languages_query = search.apply_filters(query, 'languages', "[fr,es]")
        self.assertEqual(languages_query.count(), 1)
