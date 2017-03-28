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
        data = {}
        if 'data' in event and isinstance(event['data'], dict):
            data = event['data']
        if 'body-json' in event and isinstance(event['body-json'], dict):
            data.update(event['body-json'])
        job = self.retrieve(data, 'job', 'payload')
        source = self.retrieve(job, 'source', 'job')
        resource = self.retrieve(job, 'resource_type', 'job')
        cdn_bucket = self.retrieve(job, 'cdn_bucket', 'job')
        cdn_file = self.retrieve(job, 'cdn_file', 'job')
        options = {}
        if 'options' in job:
            options = job['options']
        converter = self.converter_class(source=source, resource=resource, cdn_bucket=cdn_bucket, cdn_file=cdn_file,
                                         options=options)
        return converter.run()
