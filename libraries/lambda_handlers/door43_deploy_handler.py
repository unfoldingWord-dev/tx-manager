from __future__ import unicode_literals, print_function
from libraries.door43_tools.project_deployer import ProjectDeployer
from libraries.lambda_handlers.handler import Handler
from libraries.app.app import App
import os


class Door43DeployHandler(Handler):

    def _handle(self, event, context):
        """
        :param dict event:
        :param context:
        """
        deployer = ProjectDeployer()
        prefix = ''
        deploy_bucket =  os.environ.get('DEPLOYBUCKET')
        cdn_bucket =  os.environ.get('CDNBUCKET')
        deploy_function = os.environ.get('LAMBDA_FUNCTION_NAME')
        try:
            if 'prefix' in event:
                prefix = event['prefix']
            if 'Records' in event:
                # If we got 'Records' that means a template change was uploaded to S3 and we got the trigger
                for record in event['Records']:
                    # See if it is a notification from an S3 bucket
                    if 's3' in record:
                        bucket_name = record['s3']['bucket']['name']
                        if '-' in bucket_name:
                            prefix = bucket_name.split('-')[0] + '-'
                        App(prefix=prefix)
                        App.aws_region_name = record['awsRegion']
                        if cdn_bucket is not None:
                            App.cdn_bucket = cdn_bucket
                        if deploy_bucket is not None:
                            App.door43_bucket = deploy_bucket
                        if bucket_name == deploy_bucket:
                            deployer.redeploy_all_projects(deploy_function, True)
                        else:
                            key = record['s3']['object']['key']
                            deployer.deploy_revision_to_door43(key)
            elif 'build_log_key' in event:
                App(prefix=prefix)
                if deploy_bucket is not None:
                    App.door43_bucket = deploy_bucket
                if cdn_bucket is not None:
                    App.cdn_bucket = cdn_bucket
                deployer.deploy_revision_to_door43(event['build_log_key'])
            else:
                App(prefix=prefix)
                if deploy_bucket is not None:
                    App.door43_bucket = deploy_bucket
                if cdn_bucket is not None:
                    App.cdn_bucket = cdn_bucket
                # this is triggered manually through AWS Lambda console to update all projects
                deployer.redeploy_all_projects(deploy_function)

        except Exception:
            App.logger.exception("Project Deployer Error")
            deployer.close()
