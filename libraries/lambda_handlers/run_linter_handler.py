from __future__ import unicode_literals, print_function
from libraries.door43_tools.linter_messaging import LinterMessaging
from libraries.lambda_handlers.handler import Handler
from libraries.linters.linter_handler import LinterHandler
from libraries.resource_container.ResourceContainer import RC

class RunLinterHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Get all params, both POST and GET and JSON from the request event
        data = {}
        if 'data' in event and isinstance(event['data'], dict):
            data = event['data']
        if 'body-json' in event and event['body-json'] and isinstance(event['body-json'], dict):
            data.update(event['body-json'])
        # Set required env_vars
        args = {
            'source_zip_url': self.retrieve(data, 'source_url', 'payload'),
            'commit_data': self.retrieve(data, 'commit_data', 'payload', required=False),
            'rc': RC(manifest=self.retrieve(data, 'rc', 'payload', required=False)),
            'prefix': self.retrieve(event['vars'], 'prefix', 'Environment Vars', required=False, default=''),
            'messaging_name': self.retrieve(data, 'linter_messaging_name', 'payload', required=False, default=None),
            'single_file': self.retrieve(data, 'single_file', 'payload', required=False, default=None)  # TODO blm
        }
        linter_class = LinterHandler(**args).get_linter_class()
        ret_value = linter_class(**args).run()
        if args['messaging_name']:
            message_queue = LinterMessaging(args['messaging_name'])
            message_queue.notify_lint_job_complete(args['source_zip_url'], ret_value['success'], payload=ret_value)
        return ret_value
