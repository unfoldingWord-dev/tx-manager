from __future__ import absolute_import, unicode_literals, print_function
import unittest
from mock import patch
from moto import mock_sqs
from libraries.lambda_handlers.run_linter_handler import RunLinterHandler
from libraries.linters.linter_handler import LinterHandler


@mock_sqs
class TestLinterHandler(unittest.TestCase):

    def test_get_linter_class(self):
        self.assertEqual(LinterHandler().get_linter_class('obs').__name__, 'ObsLinter')
        self.assertEqual(LinterHandler().get_linter_class('ta').__name__, 'TaLinter')
        self.assertEqual(LinterHandler().get_linter_class('tn').__name__, 'TnLinter')
        self.assertEqual(LinterHandler().get_linter_class('tq').__name__, 'TqLinter')
        self.assertEqual(LinterHandler().get_linter_class('tw').__name__, 'TwLinter')
        self.assertEqual(LinterHandler().get_linter_class('udb').__name__, 'UdbLinter')
        self.assertEqual(LinterHandler().get_linter_class('ulb').__name__, 'UlbLinter')
        self.assertEqual(LinterHandler().get_linter_class('bible').__name__, 'UsfmLinter')
        self.assertEqual(LinterHandler().get_linter_class('something').__name__, 'MarkdownLinter')
        self.assertEqual(LinterHandler().get_linter_class('').__name__, 'MarkdownLinter')

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
