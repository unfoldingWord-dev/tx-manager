from __future__ import print_function, unicode_literals
import os
import tempfile
import boto3
import json
import logging
import time
from glob import glob
from shutil import copyfile
from libraries.aws_tools.s3_handler import S3Handler
from libraries.general_tools.file_utils import write_file, remove_tree
from libraries.door43_tools.templaters import init_template
from datetime import datetime, timedelta


class ProjectDeployer(object):
    """
    Deploys a project's revision to the door43.org bucket

    Read from the project's user dir in the cdn.door43.org bucket
    by applying the door43.org template to the raw html files
    """

    def __init__(self, cdn_bucket, door43_bucket):
        """
        :param string cdn_bucket:
        :param string door43_bucket:
        """
        self.cdn_bucket = cdn_bucket
        self.door43_bucket = door43_bucket
        self.cdn_handler = None
        self.door43_handler = None
        self.lambda_client = None
        self.logger = logging.getLogger()
        self.setup_resources()
        self.temp_dir = tempfile.mkdtemp(suffix="", prefix="deployer_")

    def setup_resources(self):
        self.cdn_handler = S3Handler(self.cdn_bucket)
        self.door43_handler = S3Handler(self.door43_bucket)
        self.lambda_client = boto3.client('lambda', region_name='us-west-2')

    def deploy_revision_to_door43(self, build_log_key):
        """
        Deploys a single revision of a project to door43.org
        :param string build_log_key:
        :return bool:
        """
        build_log = None
        try:
            build_log = self.cdn_handler.get_json(build_log_key)
        except:
            pass

        if not build_log or 'commit_id' not in build_log or 'repo_owner' not in build_log or 'repo_name' not in build_log:
            return False

        start = time.time()
        self.logger.debug("Deploying, build log: " + json.dumps(build_log))

        user = build_log['repo_owner']
        repo_name = build_log['repo_name']
        commit_id = build_log['commit_id'][:10]

        s3_commit_key = 'u/{0}/{1}/{2}'.format(user, repo_name, commit_id)
        s3_repo_key = 'u/{0}/{1}'.format(user, repo_name)
        download_key = s3_commit_key

        partial = False
        if 'part' in build_log:
            part = build_log['part']
            download_key += '/' + part
            partial = True
            self.logger.debug("found partial: " + part)

        multi = False
        if 'multiple' in build_log:
            multi = build_log['multiple']
            self.logger.debug("found multi-part merge")

        source_dir = tempfile.mkdtemp(prefix='source_', dir=self.temp_dir)
        output_dir = tempfile.mkdtemp(prefix='output_', dir=self.temp_dir)
        template_dir = tempfile.mkdtemp(prefix='template_', dir=self.temp_dir)

        resource_type = build_log['resource_type']
        template_key = 'templates/project-page.html'
        template_file = os.path.join(template_dir, 'project-page.html')

        if not multi:
            self.cdn_handler.download_dir(download_key, source_dir)
            source_dir = os.path.join(source_dir, download_key)
            self.logger.debug("Downloading {0} to {1}...".format(template_key, template_file))
            self.door43_handler.download_file(template_key, template_file)

            elapsed_seconds = int(time.time() - start)
            self.logger.debug("deploy download completed in " + str(elapsed_seconds) + " seconds")

            html_files = sorted(glob(os.path.join(source_dir, '*.html')))
            if len(html_files) < 1:
                content = ''
                if len(build_log['errors']) > 0:
                    content += """
                        <div style="text-align:center;margin-bottom:20px">
                            <i class="fa fa-times-circle-o" style="font-size: 250px;font-weight: 300;color: red"></i>
                            <br/>
                            <h2>Critical!</h2>
                            <h3>Here is what went wrong with this build:</h3>
                        </div>
                    """
                    content += '<div><ul><li>' + '</li><li>'.join(build_log['errors']) + '</li></ul></div>'
                elif len(build_log['warnings']) > 0:
                    content += """
                        <div style="text-align:center;margin-bottom:20px">
                            <i class="fa fa-exclamation-circle" style="font-size: 250px;font-weight: 300;color: yellow"></i>
                            <br/>
                            <h2>Warning!</h2>
                            <h3>Here are some problems with this build:</h3>
                        </div>
                    """
                    content += '<ul><li>' + '</li><li>'.join(build_log['warnings']) + '</li></ul>'
                else:
                    content += '<h1 class="conversion-requested">{0}</h1>'.format(build_log['message'])
                    content += '<p><i>No content is available to show for {0} yet.</i></p>'.format(repo_name)
                    content += """
                    <script type="text/javascript">setTimeout(function(){window.location.reload(1);}, 10000);</script>
                    """
                html = """
                    <html lang="en">
                        <head>
                            <title>{0}</title>
                        </head>
                        <body>
                            <div id="content">{1}</div>
                        </body>
                    </html>""".format(repo_name, content)
                repo_index_file = os.path.join(source_dir, 'index.html')
                write_file(repo_index_file, html)

            templater = init_template(resource_type, source_dir, output_dir, template_file)

            # merge the source files with the template
            templater.run()

            # update index of templated files
            index_json_fname = 'index.json'
            index_json = self.get_templater_index(s3_commit_key, index_json_fname)
            index_json['titles'] += templater.titles
            index_json['chapters'] += templater.chapters
            index_json['book_codes'] += templater.book_codes
            write_file(os.path.join(output_dir, index_json_fname), index_json)

        else:
            # merge multi-part project
            self.door43_handler.download_dir(download_key, source_dir)  # get previous templated files
            source_dir = os.path.join(source_dir, download_key)
            os.remove(os.path(source_dir, 'index.html'))  # remove index if already exists

            elapsed_seconds = int(time.time() - start)
            self.logger.debug("deploy download completed in " + str(elapsed_seconds) + " seconds")

            templater = init_template(resource_type, source_dir, output_dir, template_file)

            # restore index from previous passes
            index_json = self.get_templater_index(s3_commit_key, 'index.json')
            templater.titles = index_json['titles']
            templater.chapters = index_json['chapters']
            templater.book_codes = index_json['book_codes']
            templater.already_converted = templater.files  # do not reconvert files

            # merge the source files with the template
            templater.run()

        # Copy first HTML file to index.html if index.html doesn't exist
        html_files = sorted(glob(os.path.join(output_dir, '*.html')))
        if len(html_files) > 0:
            index_file = os.path.join(output_dir, 'index.html')
            if not os.path.isfile(index_file):
                copyfile(os.path.join(output_dir, html_files[0]), index_file)

        # Copy all other files over that don't already exist in output_dir, like css files
        for filename in sorted(glob(os.path.join(source_dir, '*'))):
            output_file = os.path.join(output_dir, os.path.basename(filename))
            if not os.path.exists(output_file) and not os.path.isdir(filename):
                copyfile(filename, output_file)

        # Upload all files to the door43.org bucket
        for root, dirs, files in os.walk(output_dir):
            for f in sorted(files):
                path = os.path.join(root, f)
                if os.path.isdir(path):
                    continue
                key = s3_commit_key + path.replace(output_dir, '')
                self.logger.debug("Uploading {0} to {1}".format(path, key))
                self.door43_handler.upload_file(path, key, 0)

        if not partial:
            # Now we place json files and make an index.html file for the whole repo
            try:
                self.door43_handler.copy(from_key='{0}/project.json'.format(s3_repo_key), from_bucket=self.cdn_bucket)
                self.door43_handler.copy(from_key='{0}/manifest.json'.format(s3_commit_key), to_key='{0}/manifest.json'.format(s3_repo_key))
                self.door43_handler.redirect(s3_repo_key, '/' + s3_commit_key)
                self.door43_handler.redirect(s3_repo_key + '/index.html', '/' + s3_commit_key)
            except Exception:
                pass

        elapsed_seconds = int(time.time() - start)
        self.logger.debug("deploy completed in " + str(elapsed_seconds) + " seconds")

        remove_tree(self.temp_dir)  # cleanup temp files
        return True

    def get_templater_index(self, s3_commit_key, index_json_fname):
        index_json = self.door43_handler.get_json(s3_commit_key + '/' + index_json_fname)
        if not index_json:
            index_json['titles'] = {}
            index_json['chapters'] = {}
            index_json['book_codes'] = {}
        return index_json

    def get_key_modified_time(self, s3_handler, source_dir, key):
        try:
            key_last_modified = s3_handler.key_modified_time(source_dir + '/' + key)
        except:
            key_last_modified = None
        return key_last_modified

    def redeploy_all_projects(self, deploy_function):
        i = 0
        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        for obj in self.cdn_handler.get_objects(prefix='u/', suffix='build_log.json'):
            i += 1
            last_modified = obj.last_modified.replace(tzinfo=None)
            if one_day_ago <= last_modified:
                continue
            self.lambda_client.invoke(
                FunctionName=deploy_function,
                InvocationType='Event',
                LogType='Tail',
                Payload=json.dumps({
                    'cdn_bucket': self.cdn_bucket,
                    'build_log_key': obj.key
                })
            )
        return True
