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

    @staticmethod
    def get_converter_module(job):
        return TxModule.query().filter(TxModule.type=='conversion')\
            .filter(TxModule.input_format.contains(job.input_format))\
            .filter(TxModule.output_format.contains(job.output_format))\
            .filter(TxModule.resource_types.contains(job.resource_type))\
            .first()

    def request_job(self, job_data):
        if 'gogs_user_token' not in job_data:
            raise Exception('"gogs_user_token" not given.')

        App.gogs_user_token = job_data['gogs_user_token']
        user = self.get_user(App.gogs_user_token)

        if not user or not user.username:
            raise Exception('Invalid user_token. User not found.')

        del job_data['gogs_user_token']
        job_data['user'] = user.username

        job = TxJob(**job_data)

        if not job.cdn_bucket:
            if not App.cdn_bucket:
                job.error_message('"cdn_bucket" not given.')
            else:
                job.cdn_bucket = App.cdn_bucket
        if not job.source:
            job.error_message('"source" url not given.')
        if not job.resource_type:
            job.error_message('"resource_type" not given.')
        if not job.input_format:
            job.error_message('"input_format" not given.')
        if not job.output_format:
            job.error_message('"output_format" not given.')

        tx_module = self.get_converter_module(job)

        if not tx_module:
            job.error_message('No converter was found to convert {0} from {1} to {2}'.format(job.resource_type,
                                                                                             job.input_format,
                                                                                             job.output_format))
        else:
            job.convert_module = tx_module.name
        job.created_at = datetime.utcnow()
        job.expires_at = job.created_at + timedelta(days=1)
        job.eta = job.created_at + timedelta(seconds=20)
        job.status = 'requested'
        job.message = 'Conversion requested...'
        job.job_id = hashlib.sha256('{0}-{1}-{2}'.format(user.username,
                                                         user.email,
                                                         job.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))).hexdigest()
        # All conversions must result in a ZIP of the converted file(s)
        output_file = 'tx/job/{0}.zip'.format(job.job_id)
        job.output = 'https://{0}/{1}'.format(App.cdn_bucket, output_file)
        job.cdn_file = output_file
        job.links = {
            "href": "{0}/tx/job/{1}".format(App.api_url, job.job_id),
            "rel": "self",
            "method": "GET"
        }
        job.insert()
        if len(job.errors):
            job.status = 'failed'
            job.message = 'Failed due to missing data'
            job.update()
            raise Exception('; '.join(job.errors))
        self.trigger_start_job(job.job_id)

        return {
            "job": dict(job),
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
            ],
        }

    def trigger_start_job(self, job_id):
        payload = {
            'data': {
                'job_id': job_id
            },
            'vars': {
                'prefix': App.prefix,
                'db_pass': App.db_pass
            }
        }
        return self.send_payload_to_start_job(payload)

    def send_payload_to_start_job(self, payload):
        App.logger.debug('Invoking the start_job lambda function with payload:')
        App.logger.debug(payload)
        start_job_function = '{0}tx_start_job'.format(App.prefix)
        App.lambda_handler().invoke(function_name=start_job_function, payload=payload, async=True)
        App.logger.debug('finished.')

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

    def start_job(self, job_id):
        job = TxJob.get(job_id)

        if not job:
            job = TxJob(job_id=job_id, success=False, message='No job with ID {} has been requested'.format(job_id))
            return job  # Job doesn't exist, return

        # Only start the job if the status is 'requested' and a started timestamp hasn't been set
        if job.status != 'requested' or job.started_at:
            return job  # Job already started, return

        job.started_at = datetime.utcnow()
        job.status = 'started'
        job.message = 'Conversion started...'
        job.log_message('Started job {0} at {1}'.format(job_id, job.started_at.strftime("%Y-%m-%dT%H:%M:%SZ")))
        success = False
        job.update()

        try:
            tx_module = self.get_converter_module(job)
            if not tx_module:
                raise Exception('No converter was found to convert {0} from {1} to {2}'
                                .format(job.resource_type, job.input_format, job.output_format))
            job.convert_module = tx_module.name
            job.update()

            payload = {
                'data': {
                    'job': dict(job),
                },
                'vars': {
                    'prefix': App.prefix
                }
            }

            converter_function = '{0}tx_convert_{1}'.format(App.prefix, tx_module.name)
            job.log_message('Telling module {0} to convert {1} and put at {2}'.format(converter_function,
                                                                                      job.source,
                                                                                      job.output))

            App.logger.debug("Payload to {0}:".format(converter_function))
            App.logger.debug(json.dumps(payload, default=json_serial))
            response = App.lambda_handler().invoke(converter_function, payload)
            App.logger.debug('finished.')

            # Get a new job since the webhook may have updated warnings
            job = TxJob.get(job_id)

            if 'errorMessage' in response:
                error = response['errorMessage']
                if error.startswith('Bad Request: '):
                    error = error[len('Bad Request: '):]
                job.error_message(error)
                App.logger.debug('Received error message from {0}: {1}'.format(converter_function, error))
            elif 'Payload' in response:
                json_data = json.loads(response['Payload'].read())
                App.logger.debug("Payload from {0}: {1}".format(converter_function, json_data))
                # The 'Payload' of the response could result in a few different formats:
                # 1) It could be that an exception was thrown in the converter code, which the API Gateway puts
                #    into a json array with "errorMessage" containing the exception message, which we handled above.
                # 2) If a "success" key is in the payload, that means our code finished with
                #    the expected results (see converters/converter.py's run() return value).
                # 3) The other possibility is for the Lambda function to not finish executing
                #    (e.g. exceeds its 5 minute execution limit). We don't currently handle this possibility.
                # Todo: Handle lambda function returning due to exceeding 5 minutes execution limit
                if 'success' in json_data:
                    success = json_data['success']
                    for message in json_data['info']:
                        if message:
                            job.log_message(message)
                    for message in json_data['errors']:
                        if message:
                            job.error_message(message)
                    for message in json_data['warnings']:
                        if message:
                            job.warning_message(message)
                    if len(json_data['errors']):
                        job.log_message('{0} function returned with errors.'.format(tx_module.name))
                    elif len(json_data['warnings']):
                        job.log_message('{0} function returned with warnings.'.format(tx_module.name))
                    else:
                        job.log_message('{0} function returned successfully.'.format(tx_module.name))
                else:
                    job.error_message('Conversion failed for unknown reason.')
            else:
                job.error_message('Conversion failed for unknown reason.')
        except Exception as e:
            job.error_message('Failed with message: {0}'.format(e.message))

        job.ended_at = datetime.utcnow()

        if not success or len(job.errors):
            job.success = False
            job.status = "failed"
            message = "Conversion failed"
            App.logger.debug("Conversion failed, success: {0}, errors: {1}".format(success, job.errors))
        elif len(job.warnings) > 0:
            job.success = True
            job.status = "warnings"
            message = "Conversion successful with warnings"
        else:
            job.success = True
            job.status = "success"
            message = "Conversion successful"

        job.message = message
        job.log_message(message)
        job.log_message('Finished job {0} at {1}'.format(job.job_id, job.ended_at.strftime("%Y-%m-%dT%H:%M:%SZ")))
        job.update()

        callback_payload = dict(job)

        callback_payload["message"] = message

        if job.callback:
            self.do_callback(job.callback, callback_payload)

        return job

    def do_callback(self, url, payload):
        if url.startswith('http'):
            headers = {"content-type": "application/json"}
            App.logger.debug('Making callback to {0} with payload:'.format(url))
            App.logger.debug(payload)
            requests.post(url, json=payload, headers=headers)
            App.logger.debug('finished.')

    @staticmethod
    def register_module(data):
        tx_module = TxModule(**data)

        if not tx_module.name:
            raise Exception('"name" not given.')
        if not tx_module.type:
            raise Exception('"type" not given.')
        if not tx_module.input_format:
            raise Exception('"input_format" not given.')
        if not tx_module.output_format:
            raise Exception('"output_format" not given.')
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
