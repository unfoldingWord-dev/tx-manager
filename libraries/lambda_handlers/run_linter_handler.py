from __future__ import unicode_literals, print_function
from libraries.door43_tools.linter_messaging import LinterMessaging
from libraries.lambda_handlers.handler import Handler
from libraries.linters.linter_handler import LinterHandler
from libraries.app.app import App


class RunLinterHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Get all params, both POST and GET and JSON from the request event
        # Gather arguments
        args = {
            'source_zip_url': self.retrieve(self.data, 'source_url', 'payload'),
            'commit_data': self.retrieve(self.data, 'commit_data', 'payload', required=False),
            'resource_id': self.retrieve(self.data, 'resource_id', 'payload', required=False),
            'single_file': self.retrieve(self.data, 'single_file', 'payload', required=False, default=None)
        }

        # Execute
        linter_class = LinterHandler.get_linter_class(args['resource_id'])
        ret_value = linter_class(**args).run()
        if App.linter_messaging_name:
            message_queue = LinterMessaging(App.linter_messaging_name)
            message_queue.notify_lint_job_complete(args['source_zip_url'], ret_value['success'], payload=ret_value)
        return ret_value
