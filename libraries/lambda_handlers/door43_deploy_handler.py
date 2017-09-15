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
        deployer = ProjectDeployer()
        prefix = ''
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
                        key = record['s3']['object']['key']
                        deployer.deploy_revision_to_door43(key)
            elif 'build_log_key' in event:
                App(prefix=prefix)
                deployer.deploy_revision_to_door43(event['build_log_key'])
            else:
                App(prefix=prefix)
                # this is triggered manually through AWS Lambda console to update all projects
                deploy_function = '{0}tx_door43_deploy'.format(App.prefix)
                deployer.redeploy_all_projects(deploy_function)

        except Exception as e:
            deployer.close()
