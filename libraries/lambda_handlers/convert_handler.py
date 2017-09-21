from __future__ import unicode_literals, print_function
import json
import requests
from libraries.app.app import App
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
        self.callback_status = 0
        self.callback_payload = None

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
        callback = self.retrieve(self.data, 'convert_callback', 'convert_callback', required=False)
        options = {}
        if 'options' in job:
            options = job['options']

        # Execute
        converter = self.converter_class(source=source, resource=resource, cdn_file=cdn_file, options=options)
        results = converter.run()
        converter.close()  # do cleanup after run
        if callback is not None:
            self.callback_payload = json.loads(json.dumps(self.data))  # clone so we can modify
            self.callback_payload['results'] = results  # add results to payload and call back
            self.do_callback(callback, self.callback_payload)
        return results

    def do_callback(self, url, payload):
        if url.startswith('http'):
            headers = {"content-type": "application/json"}
            App.logger.debug('Making callback to {0} with payload:'.format(url))
            App.logger.debug(payload)
            response = requests.post(url, json=payload, headers=headers)
            self.callback_status = response.status_code
            if (self.callback_status >= 200) and (self.callback_status < 299):
                App.logger.debug('finished.')
            else:
                App.logger.error('Error calling callback code {0}: {1}'.format(self.callback_status, response.reason))
        else:
            App.logger.error('Invalid callback url: {0}'.format(url))
