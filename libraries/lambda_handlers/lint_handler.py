from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler


class LintHandler(Handler):

    def __init__(self, *args, **kwargs):
        # Get the converter class before passing args to the parent init
        if 'linter_class' in kwargs:
            self.linter_class = kwargs.pop('linter_class')
        else:
            args = list(args)
            self.linter_class = args.pop()
        super(LintHandler, self).__init__()

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        identifier = self.retrieve(self.data, 'identifier', 'Payload', required=False, default=None)
        source_url = self.retrieve(self.data, 'source_url', 'Payload')
        commit_data = self.retrieve(self.data, 'commit_data', 'Payload', required=False)
        resource_id = self.retrieve(self.data, 'resource_id', 'Payload', required=False)
        single_file = self.retrieve(self.data, 'single_file', 'Payload', required=False, default=None)
        lint_callback = self.retrieve(self.data, 'lint_callback', 'Payload', required=False, default=None)
        cdn_file = self.retrieve(self.data, 'cdn_file', 'Payload', required=False, default=None)

        # Execute
        linter = self.linter_class(source_url=source_url, commit_data=commit_data, resource_id=resource_id,
                                   single_file=single_file, lint_callback=lint_callback, identifier=identifier,
                                   cdn_file=cdn_file)
        results = linter.run()
        linter.close()  # do cleanup after run
        return results
