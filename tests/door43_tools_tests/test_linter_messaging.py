# coding=utf-8
from __future__ import absolute_import, unicode_literals, print_function
import unittest
import time
import boto3
from string import join
from libraries.door43_tools.linter_messaging import LinterMessaging
from moto import mock_sqs


@mock_sqs
class TestLinterMessaging(unittest.TestCase):
    queue_name = "dummy-linter_complete"

    def setUp(self):
        """Runs before each test."""
        self.callbacks = 0
        try:
            sqs = boto3.resource('sqs')
            queue = sqs.create_queue(QueueName=TestLinterMessaging.queue_name, Attributes={'DelaySeconds': '5'})
            print(queue is not None)
        except Exception as e:
            pass

    def tearDown(self):
        """Runs after each test."""

    def test_messagingLIFO(self):
        # given
        q = LinterMessaging(TestLinterMessaging.queue_name)
        files_to_lint = self.generate_file_list("http://door43.org/repos/9967", 10)
        files_to_lint2 = self.generate_file_list("http://door43.org/repos/1122", 15)
        q.clear_old_lint_jobs(files_to_lint + files_to_lint2, 2)

        start = time.time()
        self.notify_lint_jobs_complete(q, files_to_lint2, False)
        self.notify_lint_jobs_complete(q, files_to_lint, True)
        elapsed_seconds = int(time.time() - start)
        print("Sending time was " + str(elapsed_seconds) + " seconds")

        # when
        success = self.wait_for_lint_jobs(q, files_to_lint)
        success2 = self.wait_for_lint_jobs(q, files_to_lint2)

        # then
        self.assertTrue(success)
        self.assertTrue(success2)

    def test_messagingFIFO(self):
        # given
        q = LinterMessaging(TestLinterMessaging.queue_name)
        files_to_lint = self.generate_file_list("http://door43.org/repos/9967", 10)
        files_to_lint2 = self.generate_file_list("http://door43.org/repos/1122", 15)
        q.clear_old_lint_jobs(files_to_lint + files_to_lint2, 2)

        start = time.time()
        self.notify_lint_jobs_complete(q, files_to_lint, True)
        self.notify_lint_jobs_complete(q, files_to_lint2, False)
        elapsed_seconds = int(time.time() - start)
        print("Sending time was " + str(elapsed_seconds) + " seconds")

        # when
        success = self.wait_for_lint_jobs(q, files_to_lint)
        success2 = self.wait_for_lint_jobs(q, files_to_lint2)

        # then
        self.assertTrue(success)
        self.assertTrue(success2)

    def test_messagingCallbackFIFO(self):
        # given
        q = LinterMessaging(TestLinterMessaging.queue_name)
        files_to_lint = self.generate_file_list("http://door43.org/repos/9967", 10)
        files_to_lint2 = self.generate_file_list("http://door43.org/repos/1122", 15)
        q.clear_old_lint_jobs(files_to_lint + files_to_lint2, 2)

        start = time.time()
        self.notify_lint_jobs_complete(q, files_to_lint, True)
        self.notify_lint_jobs_complete(q, files_to_lint2, False)
        elapsed_seconds = int(time.time() - start)
        print("Sending time was " + str(elapsed_seconds) + " seconds")

        def process_callback(x, this):
            this.callbacks += 1
            source_url = LinterMessaging.get_source_url_from_data(x)
            print("{0} - Source '{1}'=".format(this.callbacks, source_url))
            print(x)

        callback = (lambda x: process_callback(x, self))

        # when
        success = self.process_lint_jobs(callback, q, files_to_lint)
        success2 = self.process_lint_jobs(callback, q, files_to_lint2)

        # then
        self.assertTrue(success)
        self.assertTrue(success2)
        self.assertEquals(self.callbacks, len(files_to_lint) + len(files_to_lint2))

    #
    # helpers
    #

    def notify_lint_jobs_complete(self, queue, files_to_lint, success):
        for source_url in files_to_lint:
            # simulate job completion
            queue.notify_lint_job_complete(source_url, success)

    def process_lint_jobs(self, callback, queue, files_to_lint, timeout=10):
        start = time.time()
        success = queue.wait_for_lint_jobs(files_to_lint, callback=callback, timeout=timeout, visibility_timeout=2,
                                           checking_interval=0.5, max_messages_per_call=10)
        elapsed_seconds = int(time.time() - start)
        print("Waiting time was " + str(elapsed_seconds) + " seconds")
        print("done success: {0}, recvd: {1}".format(success, join(queue.recvd_payloads.keys(), "\n")))
        return success

    def wait_for_lint_jobs(self, queue, files_to_lint, timeout=10):
        start = time.time()
        success = queue.wait_for_lint_jobs(files_to_lint, timeout=timeout, visibility_timeout=2,
                                           checking_interval=0.5, max_messages_per_call=10)
        elapsed_seconds = int(time.time() - start)
        print("Waiting time was " + str(elapsed_seconds) + " seconds")
        print("done success: {0}, recvd: {1}".format(success, join(queue.recvd_payloads.keys(), "\n")))
        return success

    def generate_file_list(self, source_url, count):
        files_to_lint = ["{0}?file_{1}.usfm".format(source_url, l) for l in range(1, count+1)]
        return files_to_lint
