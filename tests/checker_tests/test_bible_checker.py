from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
from libraries.checkers.bible_checker import BibleChecker


class TestBibleChecker(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.preconvert_dir = os.path.join(self.resources_dir, 'some-bible-dir')  # Change when we have something to test
        self.temp_dir = tempfile.mkdtemp(prefix='temp_bible_')
        self.converted_dir = os.path.join(self.temp_dir, 'bible')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_success(self):
        expected_warnings = False
        expected_errors = False
        checker = BibleChecker(self.preconvert_dir, self.converted_dir)
        checker.run()
        self.verify_results(expected_errors, expected_warnings, checker)

    def verify_results(self, expected_errors, expected_warnings, checker):
        self.assertEqual(len(checker.log.logs["warning"]) > 0, expected_warnings)
        self.assertEqual(len(checker.log.logs["error"]) > 0, expected_errors)

    def test_query(self):
        from libraries.models.job import TxJob
        from libraries.aws_tools.dynamodb_handler import DynamoDBHandler
        db_handler = DynamoDBHandler('test-tx-job')
        jobs = TxJob(db_handler=db_handler).query({
            'success': {
                'condition': 'eq',
                'value': None
            }
        })
        print(jobs)
