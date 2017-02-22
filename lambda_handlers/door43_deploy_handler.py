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
                    cdn_bucket = 'cdn.door43.org'
                    door43_bucket = 'door43.org'
                    if bucket_name.startswith('test-'):
                        cdn_bucket = 'test-{0}'.format(cdn_bucket)
                        door43_bucket = 'test-{0}'.format(door43_bucket)
                    if key.endswith('.html'):
                        # If the file ends with .html, it was a change in template, so all projects are redeployed
                        ProjectDeployer(cdn_bucket, door43_bucket).redeploy_all_commits()
                    elif key.endswith('build_log.json'):
                        # Just a build_log.json file was uploaded, so we deploy this one revision
                        ProjectDeployer(cdn_bucket, door43_bucket).deploy_revision_to_door43(key)
