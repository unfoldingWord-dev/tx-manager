from __future__ import absolute_import, unicode_literals, print_function
import unittest
from manager.module import TxObject


class MyObject(TxObject):
    db_fields = [
        'field1',
        'field2'
    ]

    def __init__(self):
        self.field1 = None
        self.field2 = None
        super(MyObject, self).__init__()


class ObjectTest(unittest.TestCase):

    def test_populate(self):
        """Test populate method."""
        obj = MyObject()
        data = {
            'field1': 'value1',
            'field2': 'value2',
            'field3': 'value3'
        }
        obj.populate(data)
        self.assertTrue(hasattr(obj, 'field1'))
        self.assertEqual(obj.field2, 'value2')
        self.assertFalse(hasattr(obj, 'field3'))


if __name__ == "__main__":
    unittest.main()
