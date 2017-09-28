from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.dashboard_handler import DashboardHandler
from libraries.manager.manager import TxManager


def new_generate_dashboard(max_failures):
    return max_failures  # return the parameter for testing


class DashboardHandlerTest(TestCase):

    @mock.patch('libraries.manager.manager.TxManager.generate_dashboard')
    def test_handle(self, mock_generate_dashboard):
        mock_generate_dashboard.side_effect = new_generate_dashboard
        expected_max_failures = TxManager.MAX_FAILURES
        event = {
            'data': {}
        }
        handler = DashboardHandler()
        max_failures = handler.handle(event, expected_max_failures)
        self.assertEqual(max_failures, expected_max_failures)

    @mock.patch('libraries.manager.manager.TxManager.generate_dashboard')
    def test_dashboard_handler_max_two(self, mock_generate_dashboard):
        mock_generate_dashboard.side_effect = new_generate_dashboard
        expected_max_failures = 2
        event = {
            'data': {
                'failures': str(expected_max_failures)
            }
        }
        handler = DashboardHandler()
        max_failures = handler.handle(event, expected_max_failures)
        self.assertEqual(max_failures, expected_max_failures)
