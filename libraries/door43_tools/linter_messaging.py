from __future__ import print_function, unicode_literals
import json
from libraries.door43_tools.messaging_service import MessagingService


class LinterMessaging(MessagingService):
    def __init__(self, queue_name="linter_complete", region="us-west-2"):
        super(LinterMessaging, self).__init__(queue_name, region)

    def clear_lint_jobs(self, source_urls, timeout=2):
        """
        for safety's sake make sure there aren't leftover messages from a previous conversion
        :param source_urls: list of lint jobs referenced by the source
        :param timeout: maximum seconds to wait
        """
        self.wait_for_lint_jobs(source_urls, timeout)

    def wait_for_lint_jobs(self, source_urls, timeout=120, visibility_timeout=5):
        """
        waits for up to timeout seconds for all lint jobs to complete.  When this finishes call get_finished_jobs()
            to get the received messages as a dict
        :param source_urls: list of lint jobs referenced by the source
        :param timeout: maximum seconds to wait
        :param visibility_timeout: how long messages are hidden from other listeners
        :return: success if all messages found
        """
        return self.wait_for_messages(source_urls, timeout=timeout, visibility_timeout=visibility_timeout)

    def process_lint_jobs(self, callback, source_urls, timeout=120, visibility_timeout=5):
        """
        waits for up to timeout seconds for all sources in source_urls.  Each time a lint job finishes, func is
            called with received data.  When this finishes call get_finished_jobs() to get the received lint data
            as a dict
        :param callback: function to call back
        :param source_urls: list of lint jobs referenced by the source
        :param timeout: maximum seconds to wait
        :param visibility_timeout: how long messages are hidden from other listeners
        :return: success if all messages found
        """
        return self.process_messages(callback, source_urls, timeout=timeout, visibility_timeout=visibility_timeout)

    def get_job_data(self, source):
        """
        get job data for specific source
        :param source:
        :return:
        """
        if self.recvd_payloads:
            lint_data = self.recvd_payloads[source]
            return lint_data
        return None

    @staticmethod
    def get_source_url_from_data(data):
        return MessagingService.get_key_from_data(data)

    def notify_lint_job_complete(self, source_url, success, payload=None):
        return self.send_message(source_url, success, payload)

    def get_finished_lint_jobs(self):
        """
        get list of sources for lint jobs that have finished
        :return:
        """
        return self.get_received_messages()

    def get_unfinished_Lint_jobs(self):
        """
        get list of sources for lint jobs (from last_wait_list) that have finished yet
        :return:
        """
        return self.get_not_received_messages()
