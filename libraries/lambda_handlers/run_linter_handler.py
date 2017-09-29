from __future__ import unicode_literals, print_function
from libraries.door43_tools.linter_messaging import LinterMessaging
from libraries.lambda_handlers.handler import Handler
from libraries.linters.linter_handler import LinterHandler
from libraries.app.app import App


class RunLinterHandler(Handler):

    def __init__(self):
        super(RunLinterHandler, self).__init__()
        self.message_attempt_count = 0
        self.message_success = False

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        identity = self.retrieve(self.data, 'identity', 'Payload', required=False, default=None)
        source_url = self.retrieve(self.data, 'source_url', 'Payload')
        commit_data = self.retrieve(self.data, 'commit_data', 'Payload', required=False)
        resource_id = self.retrieve(self.data, 'resource_id', 'Payload', required=False)
        single_file = self.retrieve(self.data, 'single_file', 'Payload', required=False, default=None)
        lint_callback = self.retrieve(self.data, 'lint_callback', 'Payload', required=False, default=None)
        cdn_file = self.retrieve(self.data, 'cdn_file', 'Payload', required=False, default=None)

        # Execute
        linter_class = LinterHandler.get_linter_class(resource_id)
        linter = linter_class(source_url=source_url, commit_data=commit_data, resource_id=resource_id,
                              single_file=single_file, lint_callback=lint_callback, identity=identity,
                              cdn_file=cdn_file)
        ret_value = linter.run()
        if len(App.linter_messaging_name):
            message_queue = LinterMessaging(App.linter_messaging_name)
            while True:
                self.message_attempt_count += 1
                self.message_success = message_queue.notify_lint_job_complete(source_zip_url, ret_value['success'],
                                                                              Payload=ret_value)
                if self.message_success:
                    break

                if not message_queue.is_oversize():  # if other than oversize error
                    App.logger.error("Message failure: {0}".format(message_queue.error))
                    break

                # trim warnings list in half and try again
                warnings = ret_value['warnings']
                warnings_len = len(warnings)
                new_len = warnings_len / 2
                ret_value['warnings'] = warnings[:new_len]
                App.logger.warning("Message oversize, cut warnings from {0} to {1} lines".format(warnings_len,
                                                                                                 new_len))
        return ret_value
