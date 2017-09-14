from __future__ import print_function, unicode_literals
import json
import time
import boto3


class MessagingService(object):

    MAX_MESSAGE_SIZE = 256000
    def __init__(self, queue_name, region="us-west-2"):
        self.queue_name = queue_name
        self.region = region
        self.queue = None
        self.recvd_payloads = None
        self.last_wait_list = None
        self.message_oversize = 0
        self.error = None

    def get_connection(self):
        if not self.queue:
            try:
                sqs = boto3.resource('sqs')
                self.queue = sqs.get_queue_by_name(QueueName=self.queue_name)
            except:
                self.queue = None
        return self.queue

    def send_message(self, item_key, success, payload=None):
        if not self.get_connection():
            return False

        self.message_oversize = 0
        self.error = None
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
        message_size = len(data_json)
        if message_size >= self.MAX_MESSAGE_SIZE:
            self.message_oversize = message_size
            self.error = "message oversize: {0}".format(message_size)
            return False

        try:
            self.queue.send_message(MessageBody=data_json)
        except Exception as e:
            self.error = "message error: {0}".format(str(e))
            return False

        return True

    def clear_old_messages(self, items_to_look_for, timeout=5, checking_interval=1, max_messages_per_call=10):
        """
        for safety's sake make sure there aren't leftover messages with same key
        :param items_to_look_for:  list of items referenced by key
        :param timeout: maximum seconds to wait
        :param checking_interval: seconds to wait between checking for messages (can be fractional).  AWS charges each
                    time we check, so we don't want to be checking many times a second.
        :param max_messages_per_call: maximum number of messages to return with each check for messages (max 10)
        :return:
        """
        self.wait_for_messages(items_to_look_for, timeout=timeout, checking_interval=checking_interval,
                               max_messages_per_call=max_messages_per_call)

    def wait_for_messages(self, items_to_watch_for, callback=None, timeout=120, visibility_timeout=5,
                          checking_interval=1, max_messages_per_call=10):
        """
        waits for up to timeout seconds for all keys in items_to_watch_for.  When this finishes call get_finished_jobs()
            to get the received messages as a dict
        :param items_to_watch_for: list of items referenced by key
        :param callback: optional function to call back as each message is received
        :param timeout: maximum seconds to wait
        :param visibility_timeout: how long messages are hidden from other listeners
        :param checking_interval: seconds to wait between checking for messages (can be fractional).  AWS charges each
                    time we check, so we don't want to be checking many times a second.
        :param max_messages_per_call: maximum number of messages to return with each check for messages (max 10)
        :return: success if all messages found
        """
        self.last_wait_list = items_to_watch_for
        if not self.get_connection():
            return False

        start = time.time()
        self.recvd_payloads = {}
        timed_out = False
        while (len(self.recvd_payloads) < len(items_to_watch_for)) and not timed_out:
            messages = self.queue.receive_messages(MaxNumberOfMessages=max_messages_per_call,
                                                   VisibilityTimeout=visibility_timeout)
            for message in messages:
                if message.body:
                    recvd = json.loads(message.body, encoding="UTF-8")
                    item_key = MessagingService.get_key_from_data(recvd)
                    if item_key in items_to_watch_for:  # if this matches what we were looking for, then remove it
                                                        # from queue
                        message.delete()
                        self.recvd_payloads[item_key] = recvd
                        if callback:
                            callback(recvd)  # callback with received data

            elapsed_time = (time.time() - start)
            timed_out = elapsed_time >= timeout
            if not timed_out and len(messages) == 0:  # if we got no messages, wait before trying again
                time.sleep(checking_interval)

        success = len(self.recvd_payloads) >= len(items_to_watch_for)
        return success

    @staticmethod
    def get_key_from_data(data):
        """
        extract the key out of the received data
        :param data:
        :return:
        """
        if 'key' in data:
            item_key = data['key']
            return item_key
        return None

    def get_received_messages(self):
        """
        get list of keys for message that we have received
        :return:
        """
        return self.recvd_payloads

    def get_not_received_messages(self):
        """
        get list of keys for message (from last_wait_list) that we have not received yet
        :return:
        """
        if self.last_wait_list and self.recvd_payloads:
            unfinished = list(self.last_wait_list)
            for key in self.recvd_payloads:
                unfinished.remove(key)
            return unfinished
        return None
