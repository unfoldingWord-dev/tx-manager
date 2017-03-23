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

    def __init__(self, api_url=None, gogs_url=None, cdn_url=None, cdn_bucket=None, quiet=False,
                 aws_access_key_id=None, aws_secret_access_key=None,
                 job_table_name=None, module_table_name=None):
        """
        :param string api_url:
        :param string gogs_url:
        :param string cdn_url:
        :param string cdn_bucket:
        :param bool quiet:
        :param string aws_access_key_id:
        :param string aws_secret_access_key:
        :param string job_table_name:
        :param string module_table_name:
        """
        self.api_url = api_url
        self.gogs_url = gogs_url
        self.cdn_url = cdn_url
        self.cdn_bucket = cdn_bucket
        self.quiet = quiet
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

        self.logger = logging.getLogger('tx-manager')

        self.setup_resources()

    def setup_resources(self):
        if self.job_table_name:
            self.job_db_handler = DynamoDBHandler(self.job_table_name)
        if self.module_table_name:
            self.module_db_handler = DynamoDBHandler(self.module_table_name)
        if self.gogs_url:
            self.gogs_handler = GogsHandler(self.gogs_url)

    def debug_print(self, message):
        if not self.quiet:
            print(message)

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

        job = TxJob(data, self.quiet)

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

        module = self.get_converter_module(job)

        if not module:
            raise Exception('No converter was found to convert {0} from {1} to {2}'.format(job.resource_type,
                                                                                           job.input_format,
                                                                                           job.output_format))

        job.convert_module = module.name

        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=1)
        eta = created_at + timedelta(seconds=20)

        job.created_at = created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        job.expires_at = expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        job.eta = eta.strftime("%Y-%m-%dT%H:%M:%SZ")
        job.status = 'requested'
        job.message = 'Conversion requested...'

        job_id = hashlib.sha256('{0}-{1}-{2}'.format(user.username,
                                                     user.email,
                                                     created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))).hexdigest()
        job.job_id = job_id

        # All conversions must result in a ZIP of the converted file(s)
        output_file = 'tx/job/{0}.zip'.format(job.job_id)
        job.output = '{0}/{1}'.format(self.cdn_url, output_file)
        job.cdn_file = output_file

        job.links = {
            "href": "{0}/tx/job/{1}".format(self.api_url, job_id),
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

            module = self.get_converter_module(job)
            if not module:
                raise Exception('No converter was found to convert {0} from {1} to {2}'
                                .format(job.resource_type, job.input_format, job.output_format))

            job.converter_module = module.name
            self.update_job(job)

            payload = {
                'job': job.get_db_data(),
            }

            job.log_message('Telling module {0} to convert {1} and put at {2}'.format(module.name,
                                                                                      job.source,
                                                                                      job.output))

            headers = {"content-type": "application/json"}
            url = module.public_links[0]
            print("Payload to {0}:".format(url))
            print(json.dumps(payload))
            response = requests.post(url, json=payload, headers=headers)
            print('finished.')

            print("Response from {0}:".format(module.name))
            print(response)

            json_data = response.json()
            if json_data:
                json_data = response.json()
                if 'errorMessage' in json_data:
                    error = json_data['errorMessage']
                    if error.startswith('Bad Request: '):
                        error = error[len('Bad Request: '):]
                    job.error_message(error)

            if 'Payload' in json_data:
                payload = json_data['Payload']

                print('Payload:')
                print(json.dumps(payload))

                for message in payload['log']:
                    if message:
                        job.log_message(message)
                for message in payload['errors']:
                    if message:
                        job.error_message(message)
                for message in payload['warnings']:
                    if message:
                        job.warning_message(message)

                success = payload['success']

                if payload['errors']:
                    job.log_message('{0} function returned with errors.'.format(module.name))
                elif payload['warnings']:
                    job.log_message('{0} function returned with warnings.'.format(module.name))
                elif payload['log']:
                    job.log_message('{0} function returned.'.format(module.name))
        except Exception as e:
            job.error_message('Failed with message: {0}'.format(e.message))

        job.ended_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        if not success or len(job.errors):
            job.success = False
            job.status = "failed"
            message = "Conversion failed"
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

    @staticmethod
    def do_callback(url, payload):
        if url.startswith('http'):
            headers = {"content-type": "application/json"}
            print('Making callback to {0} with payload:'.format(url))
            print(payload)
            requests.post(url, json=payload, headers=headers)
            print('finished.')

    @staticmethod
    def make_api_gateway_for_module(module):
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
        module = TxModule(data, self.quiet)

        if not module.name:
            raise Exception('"name" not given.')
        if not module.type:
            raise Exception('"type" not given.')
        if not module.input_format:
            raise Exception('"input_format" not given.')
        if not module.output_format:
            raise Exception('"output_format" not given.')
        if not module.resource_types:
            raise Exception('"resource_types" not given.', exc_info=1)

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

    def generate_dashboard(self):
        """
        Generate page with metrics indicating configuration of tx-manager
        :param dict event:
        :param context:
        :param DynamicDBHandler:
        :param logger:
        """
        self.logger.info("Start: generateDashboard")

        dashboard = {
            'title': 'tX-Manager Dashboard',
            'body': 'No modules found'
        }

        items = sorted(self.module_db_handler.query_items(), key=lambda k: k['name'])

        if items and len(items):
            self.logger.info("  Found: " + str(len(items)) + " item[s] in tx-module")

            body = BeautifulSoup('<h1>TX-Manager Dashboard</h1><h2>Module Attributes</h2><br><table></table>',
                                 'html.parser')
            for item in items:
                # self.logger.info(json.dumps(item))
                self.logger.info(item["name"])
                body.table.append(BeautifulSoup(
                    '<tr id="' + item['name'] + '"><td class="hdr" colspan="2">' + str(item["name"]) + '</td></tr>',
                    'html.parser'))

                # TBD the following code almosts walks the db record replacing next 11 lines
                # for attr, val in item:
                #    if (attr != 'name') and (len(attr) > 0):
                #       rec += '            <tr><td class="lbl">' + attr.replace("_", " ").title() + ':</td><td>' + "lst(val)" + "</td></tr>\n"
                # rec += '<tr><td colspan="2"></td></tr>'

                body.table.append(BeautifulSoup(
                    '<tr id="' + item['name'] + '-type" class="module-type"><td class="lbl">Type:</td><td>' +
                    str(item["type"]) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + item['name'] + '-input" class="module-input"><td class="lbl">Input Format:</td><td>' +
                    str(item["input_format"]) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + item['name'] + '-output" class="module-output"><td class="lbl">Output Format:</td><td>' +
                    str(item["output_format"]) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + item['name'] + '-resource" class="module-resource"><td class="lbl">Resource Types:</td><td>' +
                    json.dumps(item["resource_types"]) + '</td></tr>',
                    'html.parser'))
                body.table.append(BeautifulSoup(
                    '<tr id="' + item['name'] + '-version" class="module-version"><td class="lbl">Version:</td><td>' +
                    str(item["version"]) + '</td></tr>',
                    'html.parser'))

                if len(item["options"]) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + item['name'] + '-options" class="module-options"><td class="lbl">Options:</td><td>' +
                        json.dumps(item["options"]) + '</td></tr>',
                        'html.parser'))

                if len(item["private_links"]) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + item['name'] + '-private-links" class="module-private-links"><td class="lbl">Private Links:</td><td>' +
                        json.dumps(item["private_links"]) + '</td></tr>',
                        'html.parser'))

                if len(item["public_links"]) > 0:
                    body.table.append(BeautifulSoup(
                        '<tr id="' + item['name'] + '-public-links" class="module-public-links"><td class="lbl">Public Links:</td><td>' +
                        json.dumps(item["public_links"]) + '</td></tr>',
                        'html.parser'))
            dashboard['body'] = body.prettify('UTF-8')
        else:
            self.logger.info("No modules found.")

        return dashboard
