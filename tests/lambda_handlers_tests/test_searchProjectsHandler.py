from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.search_projects_handler import SearchProjectsHandler
from libraries.app.app import App


class TestListJobsHandler(TestCase):

    @mock.patch('libraries.door43_tools.project_search.ProjectSearch.search_projects')
    def test_handle(self, mock_list_jobs):
        mock_list_jobs.return_value = None
        event = {
            'data': {'languages': '[en,fr]'},
        }
        handler = SearchProjectsHandler()
        self.assertIsNone(handler.handle(event, None))
