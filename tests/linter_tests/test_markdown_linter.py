from __future__ import absolute_import, unicode_literals, print_function
import os
import unittest
import tempfile
import shutil
import mock
import json
from libraries.linters.markdown_linter import MarkdownLinter
from libraries.resource_container.ResourceContainer import RC


class TestMarkdownLinter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        self.temp_dir = tempfile.mkdtemp(prefix='temp_markdown_linter_')

    def tearDown(self):
        """Runs after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @mock.patch('libraries.aws_tools.lambda_handler.LambdaHandler.invoke')
    def test_lint(self, mock_invoke):
        mock_invoke_return_payload = {
            "intro\\open-license\\title.md": [],
            "intro\\finding-answers\\sub-title.md": [],
            "intro\\gl-strategy\\01.md": [],
            "intro\\finding-answers\\01.md": [
                {
                    "lineNumber": 7,
                    "errorContext": None,
                    "ruleName": "MD007",
                    "ruleDescription": "Unordered list indentation",
                    "errorDetail": "Expected: 2; Actual: 4",
                    "ruleAlias": "ul-indent",
                    "errorRange": [
                        1,
                        6
                    ]
                }
            ],
            "intro\\translate-why\\sub-title.md": [],
            "intro\\translation-guidelines\\01.md": [],
            "intro\\gl-strategy\\title.md": [],
            "intro\\finding-answers\\title.md": [],
            "intro\\ta-intro\\title.md": [],
            "intro\\translation-guidelines\\title.md": [],
            "intro\\translate-why\\01.md": [],
            "intro\\ta-intro\\sub-title.md": [],
            "intro\\open-license\\01.md": [],
            "intro\\uw-intro\\01.md": [
                {
                    "lineNumber": 29,
                    "errorContext": None,
                    "ruleName": "MD007",
                    "ruleDescription": "Unordered list indentation",
                    "errorDetail": "Expected: 2; Actual: 4",
                    "ruleAlias": "ul-indent",
                    "errorRange": [
                        1,
                        6
                    ]
                }
            ],
            "intro\\translation-guidelines\\sub-title.md": [],
            "intro\\statement-of-faith\\sub-title.md": [],
            "intro\\uw-intro\\title.md": [],
            "intro\\uw-intro\\sub-title.md": [],
            "intro\\gl-strategy\\sub-title.md": [],
            "intro\\ta-intro\\01.md": [],
            "intro\\statement-of-faith\\title.md": [],
            "intro\\open-license\\sub-title.md": [],
            "intro\\translate-why\\title.md": [],
            "intro\\statement-of-faith\\01.md": []
        }
        mock_invoke.return_value = self.create_mock_payload(mock_invoke_return_payload)

        rc = RC(repo_name='en_ta')
        commit_data = {
            "repository": {
                "owner": {
                    "username": "Door43"
                },
                "name": "en_ta"
            }
        }
        linter = MarkdownLinter('some_url', rc=rc, commit_data=commit_data)
        linter.source_zip_file = os.path.join(self.resources_dir, 'markdown_linter', 'en_ta_intro.zip')
        results = linter.run()
        expected = {
            'success': True,
            'warnings': [
                '<a href="https://git.door43.org/Door43/en_ta/src/master/intro\\finding-answers\\01.md" target="_blank">https://git.door43.org/Door43/en_ta/src/master/intro\\finding-answers\\01.md</a> - Line7: Unordered list indentation. ',
                '<a href="https://git.door43.org/Door43/en_ta/src/master/intro\\uw-intro\\01.md" target="_blank">https://git.door43.org/Door43/en_ta/src/master/intro\\uw-intro\\01.md</a> - Line29: Unordered list indentation. '
            ]
        }
        print(results)
        self.assertEqual(len(results['warnings']), len(expected['warnings']))
        self.assertDictEqual(results, expected)

    # helper methods #

    def create_mock_payload(self, payload):
        mock_payload = TestMarkdownLinter.PayloadMock()
        mock_payload.response = json.dumps(payload)
        mock_payload = {'Payload': mock_payload}
        return mock_payload

    class PayloadMock(mock.Mock):
        response = None

        def read(self):
            return self.response
