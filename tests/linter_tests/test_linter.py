from __future__ import absolute_import, unicode_literals, print_function
import os
from tests.linter_tests.linter_unittest import LinterTestCase
from libraries.linters.linter import Linter


class MyLinter(Linter):
    def lint(self):
        self.log.warning('warning')


class TestLinter(LinterTestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def test_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Linter, None)

    def test_run(self):
        linter = MyLinter(source_zip_file=os.path.join(self.resources_dir, 'linter', 'files.zip'))
        result = linter.run()
        self.assertEqual(len(result['warnings']), 1)
        self.assertEqual(result['warnings'][0], 'warning')
