from __future__ import unicode_literals, print_function
from libraries.lambda_handlers.handler import Handler


class ConvertHandler(Handler):

    def __init__(self, *args, **kwargs):
        """
        :param args:
        :param kwargs:
        """
        # Get the converter class before passing args to the parent init
        if 'converter_class' in kwargs:
            self.converter_class = kwargs.pop('converter_class')
        else:
            args = list(args)
            self.converter_class = args.pop()
        super(ConvertHandler, self).__init__()

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        # Gather arguments
        identifier = self.retrieve(self.data, 'identifier', 'identifier', required=False)
        source_url = self.retrieve(self.data, 'source_url', 'source')
        resource_id = self.retrieve(self.data, 'resource_id', 'resource_type')
        cdn_file = self.retrieve(self.data, 'cdn_file', 'cdn_file')
        options = self.retrieve(self.data, 'options', 'options', required=False, default={})
        convert_callback = self.retrieve(self.data, 'convert_callback', 'convert_callback', required=False)

        # Execute
        converter = self.converter_class(source=source_url, resource=resource_id, cdn_file=cdn_file, options=options,
                                         convert_callback=convert_callback, identifier=identifier)
        results = converter.run()
        converter.close()  # do cleanup after run
        return results
