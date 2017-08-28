from __future__ import print_function, unicode_literals
import json
from libraries.door43_tools.messaging_service import MessagingService


class LinterMessaging(MessagingService):
    def __init__(self, queue_name="linter_complete", region="us-west-2"):
        super(LinterMessaging, self).__init__(queue_name, region)

    def clear_old_lint_jobs(self, source_urls, timeout=2, checking_interval=0.5, max_jobs_per_call=10):
        """
        for safety's sake make sure there aren't leftover messages from a previous conversion
        :param source_urls: list of lint jobs referenced by the source
        :param timeout: maximum seconds to wait
        :param checking_interval: seconds to wait between checking for finished jobs (can be fractional).  AWS charges
                    each time we check, so we don't want to be checking many times a second.
        :param max_jobs_per_call: maximum number of lint jobs to return with each check for messages (max 10)
        """
        self.clear_old_messages(source_urls, timeout=timeout, checking_interval=checking_interval,
                                max_messages_per_call=max_jobs_per_call)

    def wait_for_lint_jobs(self, source_urls, callback=None, timeout=120, visibility_timeout=5, checking_interval=1,
                           max_jobs_per_call=10):
        """
        waits for up to timeout seconds for all lint jobs to complete.  When this finishes call get_finished_jobs()
            to get the received messages as a dict
        :param source_urls: list of lint jobs referenced by the source
        :param callback: optional function to call back as each lint job completes
        :param timeout: maximum seconds to wait
        :param visibility_timeout: how long messages are hidden from other listeners
        :param checking_interval: seconds to wait between checking for finished jobs (can be fractional).  AWS charges
                    each time we check, so we don't want to be checking many times a second.
        :param max_jobs_per_call: maximum number of lint jobs to return with each check for messages (max 10)
        :return: success if all messages found
        """
        return self.wait_for_messages(source_urls, callback=callback, timeout=timeout,
                                      visibility_timeout=visibility_timeout, checking_interval=checking_interval,
                                      max_messages_per_call=max_jobs_per_call)

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
