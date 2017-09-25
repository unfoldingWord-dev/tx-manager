from __future__ import print_function, unicode_literals
import json
import os
import tempfile
from libraries.app.app import App
from libraries.general_tools.file_utils import unzip, write_file, remove_tree, remove
from libraries.general_tools.url_utils import download_file
from libraries.models.job import TxJob


class ClientLinterCallback(object):

    def __init__(self, identifier, success, info, warnings, errors):
        """
        :param string identifier:
        :param bool success:
        :param list info:
        :param list warnings:
        :param list errors:
        """
        self.identifier = identifier
        self.success = success
        self.log = info
        self.warnings = warnings
        self.errors = errors

        if not self.log:
            self.log = []
        if not self.warnings:
            self.warnings = []
        if not self.errors:
            self.errors = []
        self.temp_dir = tempfile.mkdtemp(suffix="", prefix="client_callback_")
        self.job = None

    def process_converter_callback(self):
        job_id_parts = self.identifier.split('/')
        job_id = job_id_parts[0]
        self.job = TxJob.get(job_id)

        if not self.job:
            error = 'No job found for job_id = {0}, identifier = {0}'.format(job_id, self.identifier)
            App.logger.error(error)
            raise Exception(error)

        if len(job_id_parts) == 4:
            part_count, part_id, book = job_id_parts[1:]
            App.logger.debug('Multiple project, part {0} of {1}, linted book {2}'.
                             format(part_id, part_count, book))

        if not self.success:
            msg = "Linter failed for identifier: " + self.identifier
            self.job.warnings_message(msg)
            App.logger.error(msg)
        else:
            App.logger.debug("Linter {0} results:\n{1}".format(self.identifier, '\n'.join(self.warnings)))

        has_warnings = False
        for warning in self.warnings:
            self.job.warnings_message(warning)
            has_warnings = True

        if has_warnings:
            msg = "Linter {0} has Warnings!".format(self.identifier)
            self.job.log_message(msg)
        else:
            msg = "Linter {0} completed with no warnings".format(self.identifier)
            self.job.log_message(msg)

        self.job.update()

        remove_tree(self.temp_dir)  # cleanup
        return
