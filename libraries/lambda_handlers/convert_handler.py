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
        identifier = self.retrieve(self.data, 'identifier', 'Payload', required=False)
        source = self.retrieve(self.data, 'source_url', 'Payload')
        resource = self.retrieve(self.data, 'resource_id', 'Payload')
        cdn_file = self.retrieve(self.data, 'cdn_file', 'Payload')
        options = self.retrieve(self.data, 'options', 'Payload', required=False, default={})
        convert_callback = self.retrieve(self.data, 'convert_callback', 'Payload', required=False)

        # Execute
        converter = self.converter_class(source=source, resource=resource, cdn_file=cdn_file, options=options,
                                         convert_callback=convert_callback, identifier=identifier)
        results = converter.run()
        converter.close()  # do cleanup after run
        return results
