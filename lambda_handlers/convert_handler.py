from __future__ import unicode_literals, print_function
from lambda_handlers.handler import Handler


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
        Handler.__init__(self, *args, **kwargs)

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        :return dict:
        """
        data = self.retrieve(event, 'data', 'payload')
        job = self.retrieve(data, 'job', 'payload')
        converter = self.converter_class()
        converter.source = self.retrieve(job, 'source', 'job')
        converter.resource = self.retrieve(job, 'resource_type', 'job')
        converter.cdn_bucket = self.retrieve(job, 'cdn_bucket', 'job')
        converter.cdn_file = self.retrieve(job, 'cdn_file', 'job')
        if 'options' in job:
            converter.options.update(job['options'])
        return converter.run()
