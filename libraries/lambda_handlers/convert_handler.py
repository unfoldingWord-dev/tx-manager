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
        convert_callback = self.retrieve(self.data, 'convert_callback', 'convert_callback', required=False)
        identity = self.retrieve(self.data, 'identity', 'identity', required=False)

        if 'job' in self.data:  # if parameters sent as job
            job = self.retrieve(self.data, 'job', 'payload')
            source = self.retrieve(job, 'source', 'job')
            resource = self.retrieve(job, 'resource_type', 'job')
            cdn_file = self.retrieve(job, 'cdn_file', 'job')
            options = self.retrieve(job, 'options', 'options', required=False, default={})

        else:  # if parameters not bundled into job
            source = self.retrieve(self.data, 'source', 'source')
            resource = self.retrieve(self.data, 'resource_type', 'resource_type')
            cdn_file = self.retrieve(self.data, 'cdn_file', 'cdn_file')
            options = self.retrieve(self.data, 'options', 'options', required=False, default={})

        # Execute
        converter = self.converter_class(source=source, resource=resource, cdn_file=cdn_file, options=options,
                                         convert_callback=convert_callback, identity=identity)
        results = converter.run()
        converter.close()  # do cleanup after run
        return results
