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
        job = self.retrieve(self.data, 'job', 'payload')
        source = self.retrieve(job, 'source', 'job')
        resource = self.retrieve(job, 'resource_type', 'job')
        cdn_file = self.retrieve(job, 'cdn_file', 'job')
        options = {} if 'options' not in job else job['options']
        payload = {'job': job}
        if 'convert_callback' in self.data:
            payload['convert_callback'] = self.data['convert_callback']

        # Execute
        converter = self.converter_class(source=source, resource=resource, cdn_file=cdn_file, options=options,
                                         payload=payload)
        results = converter.run()
        converter.close()  # do cleanup after run
        return results
