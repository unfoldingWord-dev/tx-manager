from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.list_endpoints_handler import ListEndpointsHandler


class TestListEndpointsHandler(TestCase):

    @mock.patch('libraries.manager.manager.TxManager.list_endpoints')
    def test_handle(self, mock_list_endpoints):
        mock_list_endpoints.return_value = None
        event = {
            'data': {}
        }
        handler = ListEndpointsHandler()
        self.assertIsNone(handler.handle(event, None))
