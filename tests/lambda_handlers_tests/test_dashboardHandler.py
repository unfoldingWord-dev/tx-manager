from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.dashboard_handler import DashboardHandler
from manager.manager import TxManager

def new_generate_dashboard( max_failures):
    return max_failures; # return the parameter for testing

class DashboardHandlerTest(TestCase):

    @mock.patch('manager.manager.TxManager.setup_resources')
    @mock.patch('manager.manager.TxManager.generate_dashboard')
    def test_handle(self, mock_generate_dashboard, mock_setup_resources):
        mock_generate_dashboard.side_effect=new_generate_dashboard
        expectedMaxFailures = TxManager.MAX_FAILURES
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
        maxFailures = handler.handle(event, expectedMaxFailures)
        self.assertEqual(maxFailures, expectedMaxFailures)

    @mock.patch('manager.manager.TxManager.setup_resources')
    @mock.patch('manager.manager.TxManager.generate_dashboard')
    def test_dashboard_handler_max_two(self, mock_generate_dashboard, mock_setup_resources):
        mock_generate_dashboard.side_effect=new_generate_dashboard
        expectedMaxFailures = 2
        event = {
            "vars" : {
                'data': {},
                'body-json': {},
                'api_url': 'https://test-api.door43.org',
                'gogs_url': 'https://git.door43.org',
                'cdn_url': 'https://test-cdn.door43.org',
                'job_table_name': 'test-tx-job',
                'module_table_name': 'test-tx-module'
            },
            "api-gateway" : {
                "params" : {
                    'querystring': {
                        'failures': str(expectedMaxFailures)
                    }
                }
            }
        }
        handler = DashboardHandler()
        maxFailures = handler.handle(event, expectedMaxFailures)
        self.assertEqual(maxFailures, expectedMaxFailures)

