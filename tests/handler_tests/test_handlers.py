from __future__ import absolute_import, unicode_literals
import functions
from mock import patch
from functions.client_callback.main import handle
from functions.client_webhook.main import handle
from functions.convert_md2html.main import handle
from functions.convert_usfm2html.main import handle
from functions.dashboard.main import handle
from functions.door43_deploy.main import handle
from functions.list_endpoints.main import handle
from functions.register_module.main import handle
from functions.request_job.main import handle
from functions.start_job.main import handle
from functions.door43_print.main import handle
from functions.run_linter.main import handle
from functions.search_projects.main import handle
from unittest import TestCase


class TestHandlers(TestCase):

    @patch('libraries.lambda_handlers.handler.Handler.handle')
    def test_handlers(self, mock_handle_return_value):
        mock_handle_return_value.return_value = None
        self.assertIsNone(functions.client_callback.main.handle({}, {}))
        self.assertIsNone(functions.client_webhook.main.handle({}, {}))
        self.assertIsNone(functions.convert_md2html.main.handle({}, {}))
        self.assertIsNone(functions.convert_usfm2html.main.handle({}, {}))
        self.assertIsNone(functions.dashboard.main.handle({}, {}))
        self.assertIsNone(functions.door43_deploy.main.handle({}, {}))
        self.assertIsNone(functions.list_endpoints.main.handle({}, {}))
        self.assertIsNone(functions.register_module.main.handle({}, {}))
        self.assertIsNone(functions.request_job.main.handle({}, {}))
        self.assertIsNone(functions.start_job.main.handle({}, {}))
        self.assertIsNone(functions.door43_print.main.handle({}, {}))
        self.assertIsNone(functions.run_linter.main.handle({}, {}))
        self.assertIsNone(functions.search_projects.main.handle({}, {}))
