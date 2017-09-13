from __future__ import absolute_import, unicode_literals, print_function
import mock
from unittest import TestCase
from libraries.lambda_handlers.request_job_handler import RequestJobHandler


class TestRequestJobHandler(TestCase):

    @mock.patch('libraries.manager.manager.TxManager.setup_job')
    def test_handle(self, mock_setup_job):
        mock_setup_job.return_value = None
        event = {
            'data': {
                "gogs_user_token": "token1",
                "cdn_bucket": "test_cdn_bucket",
                "source": "test_source",
                "resource_type": "obs",
                "input_format": "md",
                "output_format": "hstml"
            }
        }
        handler = RequestJobHandler()
        self.assertIsNone(handler.handle(event, None))
