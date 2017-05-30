from __future__ import unicode_literals, print_function
from door43_tools.project_deployer import ProjectDeployer
from lambda_handlers.handler import Handler


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
                    key = record['s3']['object']['key']
                    self.deploy(bucket_name, key)
        elif 'build_log_key' in event:
            if 'cdn_bucket' in event:
                self.deploy(event['cdn_bucket'], event['build_log_key'])
        elif 'cdn_bucket' in event:
            # this is triggered manually through AWS Lambda console to update all projects
            cdn_bucket = event['cdn_bucket']
            prefix = cdn_bucket[:-(len('cdn.door43.org'))]
            door43_bucket = '{0}door43.org'.format(prefix)
            deploy_function = '{0}tx_door43_deploy'.format(prefix)
            ProjectDeployer(cdn_bucket, door43_bucket).redeploy_all_projects(deploy_function)

    @staticmethod
    def deploy(bucket_name, key):
        cdn_bucket = 'cdn.door43.org'
        door43_bucket = 'door43.org'
        if '-' in bucket_name:
            prefix = bucket_name.split('-')[0] + '-'
            cdn_bucket = '{0}{1}'.format(prefix, cdn_bucket)
            door43_bucket = '{0}{1}'.format(prefix, door43_bucket)
        ProjectDeployer(cdn_bucket, door43_bucket).deploy_revision_to_door43(key)
