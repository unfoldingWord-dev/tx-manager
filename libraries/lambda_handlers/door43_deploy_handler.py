from __future__ import unicode_literals, print_function
from libraries.door43_tools.project_deployer import ProjectDeployer
from libraries.lambda_handlers.handler import Handler
from libraries.app.app import App


class Door43DeployHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        """
        if 'Records' in event:
            # If we got 'Records' that means a template change was uploaded to S3 and we got the trigger
            for record in event['Records']:
                # See if it is a notification from an S3 bucket
                if 's3' in record:
                    bucket_name = record['s3']['bucket']['name']
                    self.prefix_app_vars_by_bucket_prefix(bucket_name)
                    key = record['s3']['object']['key']
                    ProjectDeployer().deploy_revision_to_door43(key)
        elif 'build_log_key' in event:
            if 'cdn_bucket' in event:
                self.prefix_app_vars_by_bucket_prefix(event['cdn_bucket'])
                ProjectDeployer().deploy_revision_to_door43(event['build_log_key'])
        elif 'cdn_bucket' in event:
            # this is triggered manually through AWS Lambda console to update all projects
            self.prefix_app_vars_by_bucket_prefix(event['cdn_bucket'])
            deploy_function = '{0}tx_door43_deploy'.format(App.prefix)
            ProjectDeployer().redeploy_all_projects(deploy_function)

    @classmethod
    def prefix_app_vars_by_bucket_prefix(cls, bucket_name):
        if '-' in bucket_name:
            App.prefix = bucket_name.split('-')[0] + '-'
            App.prefix_vars()
