from __future__ import print_function, unicode_literals
import json
import time
import boto3


class MessagingService(object):

    def __init__(self, queue_name, region="us-west-2"):
        self.queue_name = queue_name
        self.region = region
        self.queue = None
        self.recvd_payloads = None

    def get_connection(self):
        if not self.queue:
            sqs = boto3.resource('sqs')
            self.queue = sqs.get_queue_by_name(QueueName=self.queue_name)
        return self.queue

    def send_message(self, item_key, success, payload=None):
        if not self.get_connection():
            return False

        data = {
            'key': item_key,
            'success': success
        }
        if payload:
            if isinstance(payload, basestring):
                data['payload'] = payload
            else:  # treat as dictionary and append data
                for k in payload:
                    data[k] = payload[k]

        data_json = json.dumps(data, encoding="UTF-8")
        self.queue.send_message(MessageBody=data_json)
        return True

    def clear_old_messages(self, items_to_look_for, timeout=5):
        self.wait_for_messages(items_to_look_for, timeout)

    def wait_for_messages(self, items_to_watch_for, timeout=120, visibility_timeout=5):
        if not self.get_connection():
            return False

        start = time.time()
        self.recvd_payloads = {}
        while (len(self.recvd_payloads) < len(items_to_watch_for)) and (int(time.time() - start) < timeout):
            for message in self.queue.receive_messages(MaxNumberOfMessages=10, VisibilityTimeout=visibility_timeout):
                if message.body:
                    recvd = json.loads(message.body, encoding="UTF-8")
                    if 'key' in recvd:
                        item_key = recvd['key']
                        if item_key in items_to_watch_for:  # if this matches what we were looking for, then remove it
                                                            # from queue
                            message.delete()
                            self.recvd_payloads[item_key] = recvd
        success = len(self.recvd_payloads) >= len(items_to_watch_for)
        return success
