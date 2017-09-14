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
        # Gather arguments
        source_zip_url = self.retrieve(self.data, 'source_url', 'payload')
        commit_data = self.retrieve(self.data, 'commit_data', 'payload', required=False)
        resource_id = self.retrieve(self.data, 'resource_id', 'payload', required=False)
        single_file = self.retrieve(self.data, 'single_file', 'payload', required=False, default=None)

        # Execute
        linter_class = LinterHandler.get_linter_class(resource_id)
        linter = linter_class(source_zip_url=source_zip_url, commit_data=commit_data, resource_id=resource_id,
                         single_file=single_file)
        ret_value = linter.run()
        if App.linter_messaging_name:
            message_queue = LinterMessaging(App.linter_messaging_name)
            while True:
                success = message_queue.notify_lint_job_complete(source_zip_url, ret_value['success'],
                                                                 payload=ret_value)
                if success:
                    break
                if message_queue.message_oversize == 0:
                    linter.log.error("Message failure: {0}".format(message_queue.error))
                    break

                # trim warnings list in half and try again
                warnings = ret_value['warnings']
                warnings_len = len(warnings)
                new_len = warnings_len / 2
                ret_value['warnings'] = warnings[:new_len]
                linter.log.warning("Message oversize, cut warnings from {0} to {1} lines".format(warnings_len,
                                                                                                 new_len))
        return ret_value
