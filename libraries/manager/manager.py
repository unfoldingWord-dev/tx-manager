from __future__ import unicode_literals, print_function
import json
import hashlib
import tempfile
import os
import requests
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup
from libraries.general_tools.data_utils import json_serial
from libraries.door43_tools.page_metrics import PageMetrics
from libraries.general_tools import file_utils
from libraries.models.job import TxJob
from libraries.models.module import TxModule
from libraries.app.app import App


class TxManager(object):
    MAX_FAILURES = 10

    def __init__(self):
        self.jobs_total = 0
        self.jobs_warnings = 0
        self.jobs_failures = 0
        self.jobs_success = 0
        self.language_views = None
        self.searches = None

    @staticmethod
    def get_user(user_token):
        return App.gogs_handler().get_user(user_token)

    def list_jobs(self, data, must_be_authenticated=True):
        if must_be_authenticated:
            if 'gogs_user_token' not in data:
                raise Exception('"gogs_user_token" not given.')
            App.gogs_user_token = data['gogs_user_token']
            user = self.get_user(App.gogs_user_token)
            if not user:
                raise Exception('Invalid user_token. User not found.')
            data['user'] = user.username
            del data['gogs_user_token']
        return TxJob.query()

    def list_endpoints(self):
        return {
            "version": "1",
            "links": [
                {
                    "href": "{0}/tx/job".format(App.api_url),
                    "rel": "list",
                    "method": "GET"
                },
                {
                    "href": "{0}/tx/job".format(App.api_url),
                    "rel": "create",
                    "method": "POST"
                },
            ]
        }

    @staticmethod
    def register_module(data):
        tx_module = TxModule(**data)

        if not tx_module.name:
            raise Exception('"name" not given.')
        if not tx_module.type:
            raise Exception('"type" not given.')
        if not tx_module.input_format:
            raise Exception('"input_format" not given.')
        if not tx_module.resource_types:
            raise Exception('"resource_types" not given.')

        tx_module.public_links.append("{0}/tx/convert/{1}".format(App.api_url, tx_module.name))
        
        old_module = TxModule.get(name=tx_module.name)
        if old_module:
            old_module.delete()
        tx_module.insert()
        return tx_module

    def generate_dashboard(self, max_failures=MAX_FAILURES):
        """
        Generate page with metrics indicating configuration of tx-manager.

        :param int max_failures:
        """
        App.logger.debug("Start: generateDashboard")

        dashboard = {
            'title': 'tX-Manager Dashboard',
            'body': 'No modules found'
        }

        items = sorted(TxModule().query(), key=lambda k: k.name)
        if items and len(items):
            module_names = []
            for item in items:
                module_names.append(item.name)

            App.logger.debug("Found: " + str(len(items)) + " item[s] in tx-module")
            App.logger.debug("Reading from Jobs table")

            registered_jobs = self.list_jobs({"convert_module": {"condition": "is_in", "value": module_names}}, False)
            total_job_count = TxJob.query().count()
            registered_job_count = registered_jobs.count()

            App.logger.debug("Finished reading from Jobs table")

            # sanity check since AWS can be slow to update job count reported in table (every 6 hours)
            if registered_job_count > total_job_count:
                total_job_count = registered_job_count

            body = BeautifulSoup('<h1>TX-Manager Dashboard - {0}</h1>'
                                 '<h2>Module Attributes</h2><br><table id="status"></table>'.format(datetime.now()),
                                 'html.parser')
            for item in items:
                module_name = item.name
                App.logger.debug(module_name)
                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '"><td class="hdr" colspan="2">' + str(module_name) + '</td></tr>',
                    'html.parser'))

                self.get_jobs_counts_for_module(registered_jobs, module_name)

                # TBD the following code almosts walks the db record replacing next 11 lines
                # for attr, val in item:
                #    if (attr != 'name') and (len(attr) > 0):
                #       rec += '            <tr><td class="lbl">' + attr.replace("_", " ").title() + ':</td><td>' + "lst(val)" + "</td></tr>\n"
                # rec += '<tr><td colspan="2"></td></tr>'

                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-type" class="module-type"><td class="lbl">Type:</td><td>' +
                    str(item.type) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-input" class="module-input"><td class="lbl">Input Format:</td><td>' +
                    json.dumps(item.input_format) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-output" class="module-output">' +
                    '<td class="lbl">Output Format:</td><td>' +
                    json.dumps(item.output_format) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-resource" class="module-resource"><td class="lbl">Resource Types:</td>'
                    '<td>' + json.dumps(item.resource_types) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-version" class="module-version"><td class="lbl">Version:</td><td>' +
                    str(item.version) + '</td></tr>',
                    'html.parser'))

                if len(item.options) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + module_name + '-options" class="module-options">' +
                        '<td class="lbl">Options:</td><td>' +
                        json.dumps(item.options) + '</td></tr>',
                        'html.parser'))

                if len(item.private_links) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + module_name + '-private-links" class="module-private-links">' +
                        '<td class="lbl">Private Links:</td><td>' +
                        json.dumps(item.private_links) + '</td></tr>',
                        'html.parser'))

                if len(item.public_links) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + module_name + '-public-links" class="module-public-links">' +
                        '<td class="lbl">Public Links:</td><td>' +
                        json.dumps(item.public_links) + '</td></tr>',
                        'html.parser'))

                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-job-success" class="module-public-links">' +
                    '<td class="lbl">Job Successes:</td><td>' +
                    str(self.jobs_success) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-job-warning" class="module-public-links">' +
                    '<td class="lbl">Job Warnings:</td><td>' +
                    str(self.jobs_warnings) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-job-failure" class="module-public-links">' +
                    '<td class="lbl">Job Failures:</td><td>' +
                    str(self.jobs_failures) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + module_name + '-job-total" class="module-public-links">' +
                    '<td class="lbl">Jobs Total:</td><td>' +
                    str(self.jobs_total) + '</td></tr>',
                    'html.parser'))

            self.get_jobs_counts(registered_jobs)
            body.table.append(BeautifulSoup(
                '<tr id="totals"><td class="hdr" colspan="2">Total Jobs</td></tr>',
                'html.parser'))
            body.table.append(BeautifulSoup(
                '<tr id="totals-job-success" class="module-public-links"><td class="lbl">Success:</td><td>' +
                str(self.jobs_success) + '</td></tr>',
                'html.parser'))
            body.table.append(BeautifulSoup(
                '<tr id="totals-job-warning" class="module-public-links"><td class="lbl">Warnings:</td><td>' +
                str(self.jobs_warnings) + '</td></tr>',
                'html.parser'))
            body.table.append(BeautifulSoup(
                '<tr id="totals-job-failure" class="module-public-links"><td class="lbl">Failures:</td><td>' +
                str(self.jobs_failures) + '</td></tr>',
                'html.parser'))
            body.table.append(BeautifulSoup(
                '<tr id="totals-job-unregistered" class="module-public-links"><td class="lbl">Unregistered:</td><td>' +
                str(total_job_count - self.jobs_total) + '</td></tr>',
                'html.parser'))
            body.table.append(BeautifulSoup(
                '<tr id="totals-job-total" class="module-public-links"><td class="lbl">Total:</td><td>' +
                str(total_job_count) + '</td></tr>',
                'html.parser'))

            # build job failures table
            job_failures = self.get_job_failures(registered_jobs, max_failures)
            body.append(BeautifulSoup('<h2>Failed Jobs</h2>', 'html.parser'))
            failure_table = BeautifulSoup('<table id="failed" cellpadding="4" border="1" ' +
                                          'style="border-collapse:collapse"></table>', 'html.parser')
            failure_table.table.append(BeautifulSoup('''
                <tr id="header">
                <th class="hdr">Time</th>
                <th class="hdr">Errors</th>
                <th class="hdr">Repo</th>
                <th class="hdr">PreConvert</th>
                <th class="hdr">Converted</th>
                <th class="hdr">Destination</th>''', 'html.parser'))

            gogs_url = App.gogs_url
            if gogs_url is None:
                gogs_url = 'https://git.door43.org'

            for i in range(0, len(job_failures)):
                item = job_failures[i]

                try:
                    identifier = item.identifier
                    owner_name, repo_name, commit_id = identifier.split('/')[:3]
                    source_sub_path = '{0}/{1}'.format(owner_name, repo_name)
                    cdn_bucket = item.cdn_bucket
                    destination_url = 'https://{0}/u/{1}/{2}/{3}/build_log.json'.format(cdn_bucket, owner_name,
                                                                                        repo_name, commit_id)
                    repo_url = gogs_url + "/" + source_sub_path
                    preconverted_url = item.source
                    converted_url = item.output
                    failure_table.table.append(BeautifulSoup(
                        '<tr id="failure-' + str(i) + '" class="module-job-id">'
                        + '<td>' + item.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") + '</td>'
                        + '<td>' + ','.join(item.errors) + '</td>'
                        + '<td><a href="' + repo_url + '">' + source_sub_path + '</a></td>'
                        + '<td><a href="' + preconverted_url + '">' + preconverted_url.rsplit('/', 1)[1] + '</a></td>'
                        + '<td><a href="' + converted_url + '">' + item.job_id + '.zip</a></td>'
                        + '<td><a href="' + destination_url + '">Build Log</a></td>'
                        + '</tr>',
                        'html.parser'))
                except Exception as e:
                    pass

            body.append(failure_table)
            self.build_language_popularity_tables(body, max_failures)
            body_html = body.prettify('UTF-8')
            dashboard['body'] = body_html

            # save to cdn in case HTTP connection times out
            try:
                self.temp_dir = tempfile.mkdtemp(suffix="", prefix="dashboard_")
                temp_file = os.path.join(self.temp_dir, "index.html")
                file_utils.write_file(temp_file, body_html)
                cdn_handler = App.cdn_s3_handler()
                cdn_handler.upload_file(temp_file, 'dashboard/index.html')
            except Exception as e:
                App.logger.debug("Could not save dashboard: " + str(e))
        else:
            App.logger.debug("No modules found.")

        App.db().close()
        return dashboard

    def build_language_popularity_tables(self, body, max_count):
        vc = PageMetrics()
        self.language_views = vc.get_language_views_sorted_by_count(reverse_sort=True, max_count=max_count)
        self.generate_highest_views_lang_table(body, self.language_views, max_count)
        self.searches = vc.get_searches_sorted_by_count(reverse_sort=True, max_count=max_count)
        self.generate_highest_searches_table(body, self.searches, max_count)

    def generate_highest_views_lang_table(self, body, views, max_count):
        body.append(BeautifulSoup('<h2>Popular Languages</h2>', 'html.parser'))
        language_popularity_table = BeautifulSoup(
            '<table id="language-popularity" cellpadding="4" border="1" style="border-collapse:collapse"></table>',
            'html.parser')
        language_popularity_table.table.append(BeautifulSoup('''
                <tr id="header">
                <th class="hdr">Views</th>
                <th class="hdr">Language Code</th>''',
                                                             'html.parser'))
        if views is not None:
            for i in range(0, max_count):
                if i >= len(views):
                    break
                item = views[i]
                try:
                    language_popularity_table.table.append(BeautifulSoup(
                        '<tr id="popular-' + str(i) + '" class="module-job-id">'
                        + '<td>' + str(item['views']) + '</td>'
                        + '<td>' + item['lang_code'] + '</td>'
                        + '</tr>',
                        'html.parser'))
                except:
                    pass
        body.append(language_popularity_table)

    def generate_highest_searches_table(self, body, views, max_count):
        body.append(BeautifulSoup('<h2>Popular Searches</h2>', 'html.parser'))
        search_popularity_table = BeautifulSoup(
            '<table id="search-popularity" cellpadding="4" border="1" style="border-collapse:collapse"></table>',
            'html.parser')
        search_popularity_table.table.append(BeautifulSoup('''
                <tr id="header">
                <th class="hdr">Views</th>
                <th class="hdr">Search</th>''',
                                                             'html.parser'))
        if views is not None:
            for i in range(0, max_count):
                if i >= len(views):
                    break
                item = views[i]
                try:
                    search_popularity_table.table.append(BeautifulSoup(
                        '<tr id="popular-' + str(i) + '" class="module-job-id">'
                        + '<td>' + str(item['views']) + '</td>'
                        + '<td>' + item['lang_code'] + '</td>'
                        + '</tr>',
                        'html.parser'))
                except:
                    pass
        body.append(search_popularity_table)

    def get_jobs_counts_for_module(self, jobs, module_name):
        self.jobs_warnings = 0
        self.jobs_failures = 0
        self.jobs_success = 0
        self.jobs_total = 0
        for job in jobs:
            name = job.convert_module
            if name == module_name:
                self.jobs_total += 1
                self.update_job_status(job)

    def get_jobs_counts(self, jobs):
        self.jobs_total = jobs.count()
        self.jobs_warnings = 0
        self.jobs_failures = 0
        self.jobs_success = 0
        for job in jobs:
            self.update_job_status(job)

    def update_job_status(self, job):
        status = job.status
        if status == "failed":
            self.jobs_failures += 1
        elif status == 'warnings':
            self.jobs_warnings += 1
        elif status != "success":
            self.jobs_failures += 1
        else:
            self.jobs_success += 1

    def get_job_failures(self, jobs, max_count):
        failed_jobs = []
        not_error = ['success', 'warnings']
        for job in jobs:
            status = job.status
            if (status not in not_error):
                failed_jobs.append(job)

        failed_jobs = sorted(failed_jobs, key=lambda k: k.created_at, reverse=True)
        top_failed_jobs = failed_jobs[:max_count]
        return top_failed_jobs
