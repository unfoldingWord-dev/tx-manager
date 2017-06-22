from __future__ import absolute_import, unicode_literals, print_function
import unittest
from libraries.models.module import Model


class MyModel(Model):
    db_keys = [
        'field1'
    ]

    db_fields = [
        'field1',
        'field2'
    ]

    def __init__(self):
        self.field1 = None
        self.field2 = None
        super(MyModel, self).__init__()


class ModelTests(unittest.TestCase):

    def test_populate(self):
        """Test populate method."""
        obj = MyModel()
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
