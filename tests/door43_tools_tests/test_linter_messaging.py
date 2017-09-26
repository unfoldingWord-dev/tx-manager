from __future__ import absolute_import, unicode_literals, print_function
import unittest
import time
import boto3
from string import join
from moto import mock_sqs
from libraries.door43_tools.linter_messaging import LinterMessaging
from libraries.app.app import App

@mock_sqs
class TestLinterMessaging(unittest.TestCase):
    queue_name = "dummy-linter_complete"

    def setUp(self):
        """Runs before each test."""
        self.callbacks = 0
        try:
            sqs = boto3.resource('sqs')
            queue = sqs.create_queue(QueueName=TestLinterMessaging.queue_name, Attributes={'DelaySeconds': '5'})
            App.logger.debug(queue is not None)
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
        App.logger.debug("Sending time was " + str(elapsed_seconds) + " seconds")

        # when
        success = self.wait_for_lint_jobs(q, files_to_lint)
        jobs1 = q.get_finished_lint_jobs()
        success2 = self.wait_for_lint_jobs(q, files_to_lint2)
        jobs2 = q.get_finished_lint_jobs()

        # then
        self.assertEquals(len(jobs1), len(files_to_lint))
        self.assertEquals(len(jobs2), len(files_to_lint2))
        unfinished_jobs = q.get_unfinished_lint_jobs()
        self.assertEquals(len(unfinished_jobs), 0)

        for job in files_to_lint2:  # these jobs should be in last list
            job_data = q.get_job_data(job)
            self.assertIsNotNone(job_data)

        for job in files_to_lint:  # these jobs should not be in last list
            job_data = q.get_job_data(job)
            self.assertIsNone(job_data)

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
        App.logger.debug("Sending time was " + str(elapsed_seconds) + " seconds")

        # when
        success = self.wait_for_lint_jobs(q, files_to_lint)
        jobs1 = q.get_finished_lint_jobs()
        success2 = self.wait_for_lint_jobs(q, files_to_lint2)
        jobs2 = q.get_finished_lint_jobs()

        # then
        self.assertEquals(len(jobs1), len(files_to_lint))
        self.assertEquals(len(jobs2), len(files_to_lint2))
        unfinished_jobs = q.get_unfinished_lint_jobs()
        self.assertEquals(len(unfinished_jobs), 0)

        for job in files_to_lint2:  # these jobs should be in last list
            job_data = q.get_job_data(job)
            self.assertIsNotNone(job_data)

        for job in files_to_lint:  # these jobs should not be in last list
            job_data = q.get_job_data(job)
            self.assertIsNone(job_data)

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
        App.logger.debug("Sending time was " + str(elapsed_seconds) + " seconds")

        def process_callback(x, this):
            this.callbacks += 1
            source_url = LinterMessaging.get_source_url_from_data(x)
            App.logger.debug("{0} - Source '{1}'=".format(this.callbacks, source_url))
            App.logger.debug(x)

        callback = (lambda x: process_callback(x, self))

        # when
        success = self.process_lint_jobs(callback, q, files_to_lint)
        success2 = self.process_lint_jobs(callback, q, files_to_lint2)

        # then
        self.assertTrue(success)
        self.assertTrue(success2)
        self.assertEquals(self.callbacks, len(files_to_lint) + len(files_to_lint2))

    def test_illegalQueue(self):
        # given
        q = LinterMessaging('invalid')

        # when
        notify_ret = q.notify_lint_job_complete("dummy", True)
        wait_ret = q.wait_for_lint_jobs([])

        # then
        self.assertFalse(notify_ret)
        self.assertFalse(wait_ret)

    def test_overSizeMessage(self):
        # given
        q = LinterMessaging(TestLinterMessaging.queue_name)
        sent_message = '#' * LinterMessaging.MAX_MESSAGE_SIZE

        # when
        notify_ret = q.notify_lint_job_complete("dummy", True, payload=sent_message)

        # then
        self.assertFalse(notify_ret)
        self.assertIsNotNone(q.error)
        self.assertTrue(q.is_oversize())

    def test_largeMessage(self):
        # given
        q = LinterMessaging(TestLinterMessaging.queue_name)
        sent_message = '#' * (LinterMessaging.MAX_MESSAGE_SIZE - 100)
        message_key = "dummy"
        q.clear_old_lint_jobs([message_key], timeout=0.1)

        # when
        notify_ret = q.notify_lint_job_complete(message_key, True, payload=sent_message)
        results_error = q.error
        results_message_oversize = q.is_oversize()
        wait_ret = q.wait_for_lint_jobs([message_key])

        # then
        self.assertTrue(notify_ret)
        self.assertTrue(wait_ret)
        self.assertIsNone(results_error)
        self.assertFalse(results_message_oversize)
        finished_jobs = q.get_finished_lint_jobs()
        self.assertEquals(len(finished_jobs), 1)
        response_message = finished_jobs[message_key]['payload']
        self.assertEquals(response_message, sent_message)

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
                                           checking_interval=0.5, max_jobs_per_call=10)
        elapsed_seconds = int(time.time() - start)
        App.logger.debug("Waiting time was " + str(elapsed_seconds) + " seconds")
        App.logger.debug("done success: {0}, recvd: {1}".format(success, join(queue.recvd_payloads.keys(), "\n")))
        return success

    def wait_for_lint_jobs(self, queue, files_to_lint, timeout=10):
        start = time.time()
        success = queue.wait_for_lint_jobs(files_to_lint, timeout=timeout, visibility_timeout=2,
                                           checking_interval=0.5, max_jobs_per_call=10)
        elapsed_seconds = int(time.time() - start)
        App.logger.debug("Waiting time was " + str(elapsed_seconds) + " seconds")
        App.logger.debug("done success: {0}, recvd: {1}".format(success, join(queue.recvd_payloads.keys(), "\n")))
        return success

    def generate_file_list(self, source_url, count):
        files_to_lint = ["{0}?file_{1}.usfm".format(source_url, l) for l in range(1, count+1)]
        return files_to_lint
