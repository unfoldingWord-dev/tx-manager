from __future__ import print_function, unicode_literals

import os
import json
from libraries.linters.linter import Linter
from libraries.aws_tools.lambda_handler import LambdaHandler
from libraries.general_tools.file_utils import read_file, get_files


class MarkdownLinter(Linter):

    def lint(self):
        """
        Checks for issues with all Markdown project, such as bad use of headers, bullets, etc.

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.usfm)
        :return:
        """
        lambda_handler = LambdaHandler()
        lint_function = '{0}tx_markdown_linter'.format(self.prefix)
        files = sorted(get_files(directory=self.source_dir, relative_paths=True, exclude=self.EXCLUDED_FILES,
                                 extensions=['.md']))
        strings = {}
        for f in files:
            path = os.path.join(self.source_dir, f)
            text = read_file(path)
            strings[f] = text
        response = lambda_handler.invoke(lint_function, {
            'options': {
                'strings': strings,
                'config': {
                    'default': True,
                    'no-hard-tabs': False,  # MD010
                    'whitespace': False,  # MD009, MD010, MD012, MD027, MD028, MD030, MD037, MD038, MD039
                    'line-length': False,  # MD013
                    'no-inline-html': False,  # MD033
                    'no-duplicate-header': False,  # MD024
                    'single-h1': False,  # MD025
                    'no-trailing-punctuation': False,  # MD026
                    'no-emphasis-as-header': False,  # MD036
                    'first-header-h1': False,  # MD002
                    'first-line-h1': False,  # MD041
                    'no-bare-urls': False,  # MD034
                }
            }
        })
        if 'errorMessage' in response:
            self.log.error(response['errorMessage'])
        elif 'Payload' in response:
            lint_data = json.loads(response['Payload'].read())
            for f in lint_data.keys():
                file_url = 'https://git.door43.org/{0}/{1}/src/master/{2}'.format(self.repo_owner, self.repo_name, f)
                for item in lint_data[f]:
                    error_context = ''
                    if item['errorContext']:
                        error_context = 'See '+item['errorContext']
                    line = '<a href="{0}" target="_blank">{0}</a> - Line{1}: {2}. {3}'. \
                        format(file_url, item['lineNumber'], item['ruleDescription'], error_context)
                    self.log.warning(line)
