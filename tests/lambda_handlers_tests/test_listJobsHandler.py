from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.list_jobs_handler import ListJobsHandler


class TestListJobsHandler(TestCase):

    @mock.patch('libraries.manager.manager.TxManager.list_jobs')
    def test_handle(self, mock_list_jobs):
        mock_list_jobs.return_value = None
        event = {
            'data': {
                'gogs_user_token': 'token1',
                'job_id': '1'
            }
        }
        handler = ListJobsHandler()
        self.assertIsNone(handler.handle(event, None))
