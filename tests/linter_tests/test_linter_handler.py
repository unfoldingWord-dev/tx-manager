from __future__ import absolute_import, unicode_literals, print_function
import unittest
from mock import patch
from moto import mock_sqs
from libraries.linters.linter import Linter
from libraries.door43_tools.linter_messaging import LinterMessaging
from libraries.lambda_handlers.run_linter_handler import RunLinterHandler
from libraries.linters.linter_handler import LinterHandler
from libraries.resource_container.ResourceContainer import RC


@mock_sqs
class TestLinterHandler(unittest.TestCase):

    def test_get_linter_class(self):
        self.assertEqual(LinterHandler('obs').get_linter_class().__name__, 'ObsLinter')
        self.assertEqual(LinterHandler('ta').get_linter_class().__name__, 'TaLinter')
        self.assertEqual(LinterHandler('tn').get_linter_class().__name__, 'TnLinter')
        self.assertEqual(LinterHandler('tq').get_linter_class().__name__, 'TqLinter')
        self.assertEqual(LinterHandler('tw').get_linter_class().__name__, 'TwLinter')
        self.assertEqual(LinterHandler('udb').get_linter_class().__name__, 'UdbLinter')
        self.assertEqual(LinterHandler('ulb').get_linter_class().__name__, 'UlbLinter')
        self.assertEqual(LinterHandler('bible').get_linter_class().__name__, 'UsfmLinter')
        self.assertEqual(LinterHandler('something').get_linter_class().__name__, 'MarkdownLinter')
        self.assertEqual(LinterHandler('').get_linter_class().__name__, 'MarkdownLinter')

    @patch('libraries.linters.linter.Linter.run')
    @patch('libraries.door43_tools.linter_messaging.LinterMessaging.notify_lint_job_complete')
    def test_run(self, mock_notify_lint_job_complete, mock_run):
        # given
        mock_run.return_value = {'success': True, 'warnings': []}
        mock_notify_lint_job_complete.return_value = True
        # rc=RC(repo_name='fr_ulb')
        event = {
            'data': {
                'source_url': 'git.door43.org/source',
                'commit_data': {
                    'repository': {
                        'name': 'dummy_repo',
                        'owner': {
                            'username': 'dummy_name'
                        }
                    }
                },
                'linter_messaging_name': 'dummy_linter_messaging_name',
            },
            'body-json': {},
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.example.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket',
                'job_table_name': 'test-tx-job',
                'module_table_name': 'test-tx-module',
                'language_stats_table_name': 'test-language-stats',
            }
        }
        handler = RunLinterHandler()
        results = handler.handle(event, None)
        self.assertIsNotNone(results)
