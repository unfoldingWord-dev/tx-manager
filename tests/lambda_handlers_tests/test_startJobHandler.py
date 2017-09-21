from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.start_job_handler import StartJobHandler


class TestStartJobHandler(TestCase):

    @mock.patch('libraries.manager.manager.TxManager.start_job')
    def test_handle(self, mock_start_job):
        mock_start_job.return_value = None
        event = {
            'data': {
                'job_id': '1234'
            },
            'vars': {
                'prefix': 'test-'
            }
        }
        handler = StartJobHandler()
        self.assertIsNone(handler.handle(event, None))
