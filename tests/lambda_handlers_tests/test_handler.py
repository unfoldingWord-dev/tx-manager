from __future__ import absolute_import, unicode_literals, print_function
from unittest import TestCase
from mock import patch
from lambda_handlers.handler import Handler


class MockHandler(Handler):

    def _handle(self, event, context):
        """
        Test if this method is called.

        :param event:
        :param context:
        :return:
        """
        pass


class TestHandler(TestCase):

    def test_inheritance(self):
        """
        This tests if the inheritance from Handler is working correctly.

        :return: None
        """

        event = {'key1': 'value1'}
        context = {'key2': 'value2'}

        handler = MockHandler()

        # noinspection PyUnresolvedReferences
        with patch.object(handler, '_handle') as mock:
            handler.handle(event, context)

        mock.assert_called_with(event, context)
