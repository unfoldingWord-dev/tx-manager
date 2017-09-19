from __future__ import absolute_import, unicode_literals, print_function
import unittest
import copy
from libraries.general_tools.data_utils import mask_fields, mask_string


class DataUtilsTests(unittest.TestCase):

    def test_mask_fields(self):
        dictionary = {
            'vars': {
                'sensitive': 'mask me'
            },
            'vars2': {
                'vars3': {
                    'sensitive': 'hide me'
                },
                'okfield': 'ok to show'
            },
            'hidden': 'hide me as well'
        }
        masked = mask_fields(copy.deepcopy(dictionary), ['sensitive', 'hidden'])
        # Make sure event wasn't touched
        self.assertNotEqual(masked['vars']['sensitive'], dictionary['vars']['sensitive'])
        self.assertNotEqual(masked['vars2']['vars3']['sensitive'], dictionary['vars2']['vars3']['sensitive'])
        self.assertNotEqual(masked['hidden'], dictionary['hidden'])
        # Make sure masked_event has been masked
        self.assertEqual(masked['vars']['sensitive'], 'ma*****')
        self.assertEqual(masked['vars2']['vars3']['sensitive'], 'hi*****')
        self.assertEqual(masked['hidden'], 'hi*************')
        # Make sure other values are not masked
        self.assertEqual(masked['vars2']['okfield'], dictionary['vars2']['okfield'])

    def test_mask_string(self):
        self.assertEqual(mask_string('test123', 1), 't******')
        self.assertEqual(mask_string('test123', 100), 'test123')
        self.assertEqual(mask_string({'test123'}), {'test123'})
        self.assertEqual(mask_string(123), 123)
