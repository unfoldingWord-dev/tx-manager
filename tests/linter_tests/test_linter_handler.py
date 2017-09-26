from __future__ import absolute_import, unicode_literals, print_function
import unittest
from mock import patch
from moto import mock_sqs
from libraries.app.app import App
from libraries.door43_tools.linter_messaging import LinterMessaging
from libraries.lambda_handlers.run_linter_handler import RunLinterHandler
from libraries.linters.linter_handler import LinterHandler


@mock_sqs
class TestLinterHandler(unittest.TestCase):

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName))

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
    def test_run_with_messaging(self, mock_notify_lint_job_complete, mock_run):
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
                }
            }
        }
        handler = RunLinterHandler()

        # when
        results = handler.handle(event, None)

        # then
        self.assertEquals(handler.message_attempt_count, 1)
        self.assertIsNotNone(results)

    @patch('libraries.linters.linter.Linter.run')
    @patch('libraries.door43_tools.linter_messaging.LinterMessaging.notify_lint_job_complete')
    def test_run_without_messaging(self, mock_notify_lint_job_complete, mock_run):
        # given
        mock_run.return_value = {'success': True, 'warnings': []}
        mock_notify_lint_job_complete.return_value = True
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
                }
            }
        }
        handler = RunLinterHandler()
        App.linter_messaging_name = ''

        # when
        results = handler.handle(event, None)

        # then
        self.assertEquals(handler.message_attempt_count, 0)
        self.assertIsNotNone(results)

    @patch('libraries.linters.linter.Linter.run')
    @patch('libraries.door43_tools.linter_messaging.LinterMessaging.notify_lint_job_complete')
    @patch('libraries.door43_tools.linter_messaging.LinterMessaging.is_oversize')
    def test_run_with_messaging_oversize(self, mock_is_oversize, mock_notify_lint_job_complete, mock_run):
        # given
        warning = 'Warning ' + '#' * 100
        warnings = []
        for i in range(0, (LinterMessaging.MAX_MESSAGE_SIZE / 100) + 1):
            warnings.append(warning)
        mock_run.return_value = {'success': True, 'warnings': warnings}
        mock_notify_lint_job_complete.side_effect = [False, True]
        mock_is_oversize.side_effect = [True, False]
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
                }
            }
        }
        handler = RunLinterHandler()

        # when
        results = handler.handle(event, None)

        # then
        self.assertEquals(handler.message_attempt_count, 2)
        self.assertIsNotNone(results)

    @patch('libraries.linters.linter.Linter.run')
    @patch('libraries.door43_tools.linter_messaging.LinterMessaging.notify_lint_job_complete')
    @patch('libraries.door43_tools.linter_messaging.LinterMessaging.is_oversize')
    def test_run_with_messaging_fail(self, mock_is_oversize, mock_notify_lint_job_complete, mock_run):
        # given
        warning = 'Warning ' + '#' * 100
        warnings = []
        for i in range(0, (LinterMessaging.MAX_MESSAGE_SIZE / 100) + 1):
            warnings.append(warning)
        mock_run.return_value = {'success': True, 'warnings': warnings}
        mock_notify_lint_job_complete.return_value = False
        mock_is_oversize.return_value = False
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
                }
            }
        }
        handler = RunLinterHandler()

        # when
        results = handler.handle(event, None)

        # then
        self.assertEquals(handler.message_attempt_count, 1)
        self.assertIsNotNone(results)
