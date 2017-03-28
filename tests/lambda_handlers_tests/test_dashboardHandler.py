from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.dashboard_handler import DashboardHandler


class TestListJobsHandler(TestCase):

    @mock.patch('manager.manager.TxManager.setup_resources')
    @mock.patch('manager.manager.TxManager.generate_dashboard')
    def test_handle(self, mock_generate_dashboard, mock_setup_resources):
        mock_generate_dashboard.return_value = None
        event = {
            'data': {},
            'body-json': {},
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.exmaple.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket',
                'job_table_name': 'test-tx-job',
                'module_table_name': 'test-tx-module'
            }
        }
        handler = DashboardHandler()
        self.assertIsNone(handler.handle(event, None))

