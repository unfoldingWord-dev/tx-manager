from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from lambda_handlers.list_jobs_handler import ListJobsHandler


class TestListJobsHandler(TestCase):

    @mock.patch('manager.manager.TxManager.setup_resources')
    @mock.patch('manager.manager.TxManager.list_jobs')
    def test_handle(self, mock_setup_resources, mock_list_jobs):
        mock_setup_resources.return_value = None
        mock_list_jobs.return_value = None
        event = {
            'data': {
                'gogs_user_token': 'token1',
                'job_id': '1'
            },
            'vars': {
                'gogs_url': 'https://git.example.com',
                'cdn_url': 'https://cdn.exmaple.com',
                'api_url': 'https://api.example.com',
                'cdn_bucket': 'cdn_test_bucket'
            }
        }
        handler = ListJobsHandler()
        self.assertIsNone(handler.handle(event, None))
