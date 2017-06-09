from __future__ import unicode_literals, print_function
import json
import hashlib
import requests
import logging
from datetime import datetime
from datetime import timedelta
from bs4 import BeautifulSoup
from aws_tools.dynamodb_handler import DynamoDBHandler
from gogs_tools.gogs_handler import GogsHandler
from job import TxJob
from module import TxModule


class TxManager(object):
    JOB_TABLE_NAME = 'tx-job'
    MODULE_TABLE_NAME = 'tx-module'
    MAX_FAILURES = 10

    def __init__(self, api_url=None, gogs_url=None, cdn_url=None, cdn_bucket=None,
                 aws_access_key_id=None, aws_secret_access_key=None,
                 job_table_name=None, module_table_name=None):
        """
        :param string api_url:
        :param string gogs_url:
        :param string cdn_url:
        :param string cdn_bucket:
        :param string aws_access_key_id:
        :param string aws_secret_access_key:
        :param string job_table_name:
        :param string module_table_name:
        """
        self.api_url = api_url
        self.gogs_url = gogs_url
        self.cdn_url = cdn_url
        self.cdn_bucket = cdn_bucket
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.job_table_name = job_table_name
        self.module_table_name = module_table_name

        if not self.job_table_name:
            self.job_table_name = TxManager.JOB_TABLE_NAME
        if not self.module_table_name:
            self.module_table_name = TxManager.MODULE_TABLE_NAME

        self.job_db_handler = None
        self.module_db_handler = None
        self.gogs_handler = None

        self.jobs_total = 0
        self.jobs_warnings = 0
        self.jobs_failures = 0
        self.jobs_success = 0

        self.logger = logging.getLogger()

        self.setup_resources()

    def setup_resources(self):
        if self.job_table_name:
            self.job_db_handler = DynamoDBHandler(self.job_table_name)
        if self.module_table_name:
            self.module_db_handler = DynamoDBHandler(self.module_table_name)
        if self.gogs_url:
            self.gogs_handler = GogsHandler(self.gogs_url)

    def get_user(self, user_token):
        return self.gogs_handler.get_user(user_token)

    def get_converter_module(self, job):
        modules = self.query_modules()
        for module in modules:
            if job.resource_type in module.resource_types:
                if job.input_format in module.input_format:
                    if job.output_format in module.output_format:
                        return module
        return None

    def setup_job(self, data):
        if 'gogs_user_token' not in data:
            raise Exception('"gogs_user_token" not given.')

        user = self.get_user(data['gogs_user_token'])

        if not user or not user.username:
            raise Exception('Invalid user_token. User not found.')

        del data['gogs_user_token']
        data['user'] = user.username

        job = TxJob(data)

        if not job.cdn_bucket:
            if not self.cdn_bucket:
                raise Exception('"cdn_bucket" not given.')
            else:
                job.cdn_bucket = self.cdn_bucket
        if not job.source:
            raise Exception('"source" url not given.')
        if not job.resource_type:
            raise Exception('"resource_type" not given.')
        if not job.input_format:
            raise Exception('"input_format" not given.')
        if not job.output_format:
            raise Exception('"output_format" not given.')

        converter_module = self.get_converter_module(job)

        if not converter_module:
            raise Exception('No converter was found to convert {0} from {1} to {2}'.format(job.resource_type,
                                                                                           job.input_format,
                                                                                           job.output_format))
        job.convert_module = converter_module.name
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=1)
        eta = created_at + timedelta(seconds=20)
        job.created_at = created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        job.expires_at = expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        job.eta = eta.strftime("%Y-%m-%dT%H:%M:%SZ")
        job.status = 'requested'
        job.message = 'Conversion requested...'
        job.job_id = hashlib.sha256('{0}-{1}-{2}'.format(user.username,
                                                         user.email,
                                                         created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))).hexdigest()
        # All conversions must result in a ZIP of the converted file(s)
        output_file = 'tx/job/{0}.zip'.format(job.job_id)
        job.output = '{0}/{1}'.format(self.cdn_url, output_file)
        job.cdn_file = output_file
        job.links = {
            "href": "{0}/tx/job/{1}".format(self.api_url, job.job_id),
            "rel": "self",
            "method": "GET"
        }
        # Saving this to the DynamoDB will start trigger a DB stream which will call
        # tx-manager again with the job info (see run() function)
        self.insert_job(job)
        return {
            "job": job.get_db_data(),
            "links": [
                {
                    "href": "{0}/tx/job".format(self.api_url),
                    "rel": "list",
                    "method": "GET"
                },
                {
                    "href": "{0}/tx/job".format(self.api_url),
                    "rel": "create",
                    "method": "POST"
                },
            ],
        }

    def get_job_count(self):
        """
        get number of jobs in database - one caveat is that this value may be off since AWS only updates it every 6 hours
        :return: 
        """
        return self.job_db_handler.get_item_count()

    def list_jobs(self, data, must_be_authenticated=True):
        if must_be_authenticated:
            if 'gogs_user_token' not in data:
                raise Exception('"gogs_user_token" not given.')
            user = self.get_user(data['gogs_user_token'])
            if not user:
                raise Exception('Invalid user_token. User not found.')
            data['user'] = user.username
            del data['gogs_user_token']
        jobs = self.query_jobs(data)
        ret = []
        if jobs and len(jobs):
            for job in jobs:
                ret.append(job.get_db_data())
        return ret

    def list_endpoints(self):
        return {
            "version": "1",
            "links": [
                {
                    "href": "{0}/tx/job".format(self.api_url),
                    "rel": "list",
                    "method": "GET"
                },
                {
                    "href": "{0}/tx/job".format(self.api_url),
                    "rel": "create",
                    "method": "POST"
                },
            ]
        }

    def start_job(self, job_id):
        job = self.get_job(job_id)

        if not job.job_id:
            job.job_id = job_id
            job.success = False
            job.message = 'No job with ID {} has been requested'.format(job_id)
            return job.get_db_data()  # Job doesn't exist, return

        # Only start the job if the status is 'requested' and a started timestamp hasn't been set
        if job.status != 'requested' or job.started_at:
            return job.get_db_data()  # Job already started, return

        job.started_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        job.status = 'started'
        job.message = 'Conversion started...'
        job.log_message('Started job {0} at {1}'.format(job_id, job.started_at))
        success = False

        try:
            self.update_job(job)
            converter_module = self.get_converter_module(job)
            if not converter_module:
                raise Exception('No converter was found to convert {0} from {1} to {2}'
                                .format(job.resource_type, job.input_format, job.output_format))

            job.converter_module = converter_module.name
            self.update_job(job)

            payload = {
                'job': job.get_db_data(),
            }

            job.log_message('Telling module {0} to convert {1} and put at {2}'.format(converter_module.name,
                                                                                      job.source,
                                                                                      job.output))

            headers = {"content-type": "application/json"}
            url = converter_module.public_links[0]
            self.logger.debug("Payload to {0}:".format(url))
            self.logger.debug(json.dumps(payload))
            response = requests.post(url, json=payload, headers=headers)
            self.logger.debug('finished.')

            self.logger.debug("Response from {0}:".format(converter_module.name))
            self.logger.debug(response.json())

            json_data = response.json()
            if json_data:
                # The json_data of the response could result in a few different formats:
                # 1) It could be that an exception was thrown in the converter code, which the API Gateway puts
                #    into a json array with "errorMessage" containing the exception message.
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
                        job.log_message('{0} function returned with errors.'.format(converter_module.name))
                    elif len(json_data['warnings']):
                        job.log_message('{0} function returned with warnings.'.format(converter_module.name))
                    else:
                        job.log_message('{0} function returned successfully.'.format(converter_module.name))
                elif 'errorMessage' in json_data or 'message' in json_data:
                    error = json_data.get('errorMessage', json_data.get('message'))
                    if error.startswith('Bad Request: '):
                        error = error[len('Bad Request: '):]
                    job.error_message(error)
                else:
                    job.error_message('Conversion failed for unknown reason: {0}'.format(json_data))
        except Exception as e:
            job.error_message('Failed with message: {0}'.format(e.message))

        job.ended_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        if not success or len(job.errors):
            job.success = False
            job.status = "failed"
            message = "Conversion failed"
            self.logger.debug("Conversion failed, success: {0}, errors: {1}".format(success, job.errors))
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
        job.log_message('Finished job {0} at {1}'.format(job.job_id, job.ended_at))

        self.update_job(job)

        callback_payload = job.get_db_data()

        callback_payload["message"] = message

        if job.callback:
            self.do_callback(job.callback, callback_payload)

        return job.get_db_data()

    def do_callback(self, url, payload):
        if url.startswith('http'):
            headers = {"content-type": "application/json"}
            self.logger.debug('Making callback to {0} with payload:'.format(url))
            self.logger.debug(payload)
            requests.post(url, json=payload, headers=headers)
            self.logger.debug('finished.')

    def make_api_gateway_for_module(self, module):
        # lambda_func_name = module['name']
        # AWS_LAMBDA_API_ID = '7X97xCLPDE16Jep5Zv85N6zy28wcQfJz79E2H3ln'
        # # of 'tx-manager_api_key'
        # # or fkcr7r4dz9
        # # or 7X97xCLPDE16Jep5Zv85N6zy28wcQfJz79E2H3ln
        # AWS_REGION = 'us-west-2'
        #
        # api_client = boto3.client('apigateway')
        # aws_lambda = boto3.client('lambda')
        #
        # ## create resource
        # resource_resp = api_client.create_resource(
        #     restApiId=AWS_LAMBDA_API_ID,
        #     parentId='foo', # resource id for the Base API path
        #     pathPart=lambda_func_name
        # )
        #
        # ## create POST method
        # put_method_resp = api_client.put_method(
        #     restApiId=AWS_LAMBDA_API_ID,
        #     resourceId=resource_resp['id'],
        #     httpMethod="POST",
        #     authorizationType="NONE",
        #     apiKeyRequired=True,
        # )
        #
        # lambda_version = aws_lambda.meta.service_model.api_version
        #
        # uri_data = {
        #     "aws-region": AWS_REGION,
        #     "api-version": lambda_version,
        #     "aws-acct-id": "xyzABC",
        #     "lambda-function-name": lambda_func_name,
        # }
        #
        # uri = "arn:aws:apigateway:{aws-region}:lambda:path/{api-version}/functions/arn:aws:lambda:{aws-region}:
        #        {aws-acct-id}:function:{lambda-function-name}/invocations".format(**uri_data)
        #
        # ## create integration
        # integration_resp = api_client.put_integration(
        #     restApiId=AWS_LAMBDA_API_ID,
        #     resourceId=resource_resp['id'],
        #     httpMethod="POST",
        #     type="AWS",
        #     integrationHttpMethod="POST",
        #     uri=uri,
        # )
        #
        # api_client.put_integration_response(
        #     restApiId=AWS_LAMBDA_API_ID,
        #     resourceId=resource_resp['id'],
        #     httpMethod="POST",
        #     statusCode="200",
        #     selectionPattern=".*"
        # )
        #
        # ## create POST method response
        # api_client.put_method_response(
        #     restApiId=AWS_LAMBDA_API_ID,
        #     resourceId=resource_resp['id'],
        #     httpMethod="POST",
        #     statusCode="200",
        # )
        #
        # uri_data['aws-api-id'] = AWS_LAMBDA_API_ID
        # source_arn = "arn:aws:execute-api:{aws-region}:{aws-acct-id}:
        #               {aws-api-id}/*/POST/{lambda-function-name}".format(**uri_data)
        #
        # aws_lambda.add_permission(
        #     FunctionName=lambda_func_name,
        #     StatementId=uuid.uuid4().hex,
        #     Action="lambda:InvokeFunction",
        #     Principal="apigateway.amazonaws.com",
        #     SourceArn=source_arn
        # )
        #
        # # state 'your stage name' was already created via API Gateway GUI
        # api_client.create_deployment(
        #     restApiId=AWS_LAMBDA_API_ID,
        #     stageName="your stage name",
        # )
        return

    def register_module(self, data):
        module = TxModule(data)

        if not module.name:
            raise Exception('"name" not given.')
        if not module.type:
            raise Exception('"type" not given.')
        if not module.input_format:
            raise Exception('"input_format" not given.')
        if not module.output_format:
            raise Exception('"output_format" not given.')
        if not module.resource_types:
            raise Exception('"resource_types" not given.')

        module.public_links.append("{0}/tx/convert/{1}".format(self.api_url, module.name))
        self.insert_module(module)
        self.make_api_gateway_for_module(module)  # Todo: develop this function
        return module.get_db_data()

    def insert_job(self, job):
        job_data = job.get_db_data()
        self.job_db_handler.insert_item(job_data)

    def query_jobs(self, data=None):
        items = self.job_db_handler.query_items(data)
        jobs = []
        if items and len(items):
            for item in items:
                jobs.append(TxJob(item))
        return jobs

    def get_job(self, job_id):
        return TxJob(self.job_db_handler.get_item({'job_id': job_id}))

    def update_job(self, job):
        return self.job_db_handler.update_item({'job_id': job.job_id}, job.get_db_data())

    def delete_job(self, job):
        return self.job_db_handler.delete_item({'job_id': job.job_id})

    def insert_module(self, module):
        module_data = module.get_db_data()
        self.module_db_handler.insert_item(module_data)

    def query_modules(self, data=None):
        items = self.module_db_handler.query_items(data)
        modules = []
        if items and len(items):
            for item in items:
                modules.append(TxModule(item))
        return modules

    def get_module(self, name):
        return TxModule(self.module_db_handler.get_item({'name': name}))

    def update_module(self, module):
        return self.module_db_handler.update_item({'name': module.name}, module.get_db_data())

    def delete_module(self, module):
        return self.module_db_handler.delete_item({'name': module.name})

    def generate_dashboard(self, max_failures=MAX_FAILURES):
        """
        Generate page with metrics indicating configuration of tx-manager.

        :param int max_failures:
        """
        self.logger.debug("Start: generateDashboard")

        dashboard = {
            'title': 'tX-Manager Dashboard',
            'body': 'No modules found'
        }

        items = sorted(self.module_db_handler.query_items(), key=lambda k: k['name'])
        if items and len(items):
            moduleNames = []
            for item in items:
                moduleNames.append(item["name"])

            registeredJobs = self.list_jobs({ "convert_module" : { "condition" : "is_in", "value" : moduleNames}
                                    }, False)
            totalJobCount = self.get_job_count()
            registeredJobCount = len(registeredJobs)
            if registeredJobCount > totalJobCount: # sanity check since AWS can be slow to update job count reported in table (every 6 hours)
                totalJobCount = registeredJobCount

            self.logger.debug("Found: " + str(len(items)) + " item[s] in tx-module")

            body = BeautifulSoup('<h1>TX-Manager Dashboard</h1><h2>Module Attributes</h2><br><table id="status"></table>',
                                 'html.parser')
            for item in items:
                moduleName = item["name"]
                self.logger.debug(moduleName)
                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '"><td class="hdr" colspan="2">' + str(moduleName) + '</td></tr>',
                    'html.parser'))

                jobs = self.get_jobs_for_module(registeredJobs, moduleName)
                self.get_jobs_counts(jobs)

                # TBD the following code almosts walks the db record replacing next 11 lines
                # for attr, val in item:
                #    if (attr != 'name') and (len(attr) > 0):
                #       rec += '            <tr><td class="lbl">' + attr.replace("_", " ").title() + ':</td><td>' + "lst(val)" + "</td></tr>\n"
                # rec += '<tr><td colspan="2"></td></tr>'

                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-type" class="module-type"><td class="lbl">Type:</td><td>' +
                    str(item["type"]) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-input" class="module-input"><td class="lbl">Input Format:</td><td>' +
                    json.dumps(item["input_format"]) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-output" class="module-output"><td class="lbl">Output Format:</td><td>' +
                    json.dumps(item["output_format"]) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-resource" class="module-resource"><td class="lbl">Resource Types:</td><td>' +
                    json.dumps(item["resource_types"]) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-version" class="module-version"><td class="lbl">Version:</td><td>' +
                    str(item["version"]) + '</td></tr>',
                    'html.parser'))

                if len(item["options"]) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + moduleName + '-options" class="module-options"><td class="lbl">Options:</td><td>' +
                        json.dumps(item["options"]) + '</td></tr>',
                        'html.parser'))

                if len(item["private_links"]) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + moduleName + '-private-links" class="module-private-links"><td class="lbl">Private Links:</td><td>' +
                        json.dumps(item["private_links"]) + '</td></tr>',
                        'html.parser'))

                if len(item["public_links"]) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + moduleName + '-public-links" class="module-public-links"><td class="lbl">Public Links:</td><td>' +
                        json.dumps(item["public_links"]) + '</td></tr>',
                        'html.parser'))

                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-job-success" class="module-public-links"><td class="lbl">Job Successes:</td><td>' +
                    str(self.jobs_success) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-job-warning" class="module-public-links"><td class="lbl">Job Warnings:</td><td>' +
                    str(self.jobs_warnings) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-job-failure" class="module-public-links"><td class="lbl">Job Failures:</td><td>' +
                    str(self.jobs_failures) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + moduleName + '-job-total" class="module-public-links"><td class="lbl">Jobs Total:</td><td>' +
                    str(self.jobs_total) + '</td></tr>',
                    'html.parser'))

            self.get_jobs_counts(registeredJobs)
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
                str(totalJobCount - self.jobs_total) + '</td></tr>',
                'html.parser'))
            body.table.append(BeautifulSoup(
                '<tr id="totals-job-total" class="module-public-links"><td class="lbl">Total:</td><td>' +
                str(totalJobCount) + '</td></tr>',
                'html.parser'))

            # build job failures table

            jobFailures = self.get_job_failures(registeredJobs)
            body.append(BeautifulSoup('<h2>Failed Jobs</h2>', 'html.parser'))
            failureTable = BeautifulSoup('<table id="failed" cellpadding="4" border="1" style="border-collapse:collapse"></table>','html.parser')
            failureTable.table.append(BeautifulSoup(
                '<tr id="header">'
                '<th class="hdr">Time</th>'
                '<th class="hdr">Errors</th>'
                '<th class="hdr">Repo</th>'
                '<th class="hdr">PreConvert</th>'
                '<th class="hdr">Converted</th>'
                '<th class="hdr">Destination</th>'
                'html.parser'))

            gogs_url = self.gogs_url
            if gogs_url == None :
                gogs_url = 'https://git.door43.org'

            for i in range(0, max_failures):
                if i >= len(jobFailures):
                    break

                item = jobFailures[i]

                try :
                    identifier = item['identifier']
                    owner_name, repo_name, commit_id = identifier.split('/')
                    sourceSubPath = '{0}/{1}'.format(owner_name, repo_name)
                    cdn_bucket = item['cdn_bucket']
                    destinationUrl = 'https://{0}/u/{1}/{2}/{3}/build_log.json'.format(cdn_bucket, owner_name, repo_name, commit_id)
                    repoUrl = gogs_url + "/" + sourceSubPath
                    preconvertedUrl = item['source']
                    convertedUrl = item['output']
                    failureTable.table.append(BeautifulSoup(
                        '<tr id="failure-' + str(i) + '" class="module-job-id">'
                        + '<td>' + item['created_at'] + '</td>'
                        + '<td>' + ','.join(item['errors']) + '</td>'
                        + '<td><a href="' + repoUrl + '">' + sourceSubPath + '</a></td>'
                        + '<td><a href="' + preconvertedUrl + '">' + preconvertedUrl.rsplit('/', 1)[1] + '</a></td>'
                        + '<td><a href="' + convertedUrl + '">' + item['job_id'] + '.zip</a></td>'
                        + '<td><a href="' + destinationUrl + '">Build Log</a></td>'
                        + '</tr>',
                        'html.parser'))
                except:
                    pass

            body.append(failureTable)
            dashboard['body'] = body.prettify('UTF-8')
        else:
            self.logger.debug("No modules found.")

        return dashboard

    def get_jobs_for_module(self, jobs, moduleName):
        jobsInModule = []
        for job in jobs:
            if "convert_module" in job:
                name = job["convert_module"]
                if name == moduleName:
                    jobsInModule.append(job)

        return jobsInModule

    def get_jobs_counts(self, jobs):
        self.jobs_total = len(jobs)
        self.jobs_warnings = 0
        self.jobs_failures = 0
        self.jobs_success = 0
        for job in jobs:
            errors = job['errors']
            if len(errors) > 0:
                self.jobs_failures+=1
                continue

            warnings = job['warnings']
            if len(warnings) > 0:
                self.jobs_warnings+=1
                continue

            self.jobs_success+=1

    def get_job_failures(self, jobs):
        failedJobs = []
        for job in jobs:
            errors = job['errors']
            if len(errors) > 0:
                failedJobs.append(job)

        failedJobs = sorted(failedJobs, key=lambda k: k['created_at'], reverse=True)
        return failedJobs

