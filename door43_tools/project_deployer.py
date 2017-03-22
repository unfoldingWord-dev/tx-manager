from __future__ import print_function, unicode_literals
import os
import sys
import tempfile
from glob import glob
from shutil import copyfile
from aws_tools.s3_handler import S3Handler
from general_tools.file_utils import write_file
from door43_tools import templaters


class ProjectDeployer(object):
    """
    Deploys a project's revision to the door43.org bucket from the project's user dir in the cdn.door43.org bucket
    by applying the door43.org template to the raw html files
    """

    def __init__(self, cdn_bucket, door43_bucket, s3_handler_class=S3Handler):
        """
        :param string cdn_bucket: 
        :param string door43_bucket: 
        :param class s3_handler_class
        """
        self.cdn_bucket = cdn_bucket
        self.door43_bucket = door43_bucket
        self.s3_handler_class = s3_handler_class

    def deploy_revision_to_door43(self, build_log_key):
        cdn_handler = S3Handler(self.cdn_bucket)
        door43_handler = S3Handler(self.door43_bucket)

        build_log = None
        try:
            build_log = cdn_handler.get_json(build_log_key)
        except:
            pass

        print(build_log)

        if not build_log or 'commit_id' not in build_log or 'repo_owner' not in build_log or 'repo_name' not in build_log:
            return False

        user = build_log['repo_owner']
        repo_name = build_log['repo_name']
        commit_id = build_log['commit_id'][:10]

        s3_commit_key = 'u/{0}/{1}/{2}'.format(user, repo_name, commit_id)
        s3_repo_key = 'u/{0}/{1}'.format(user, repo_name)

        source_dir = tempfile.mkdtemp(prefix='source_')
        output_dir = tempfile.mkdtemp(prefix='output_')
        template_dir = tempfile.mkdtemp(prefix='template_')

        cdn_handler.download_dir(s3_commit_key, source_dir)
        source_dir = os.path.join(source_dir, s3_commit_key)

        # determining the template and templater from the resource_type, use general if not found
        try:
            templater_class = self.str_to_class('templaters.{0}Templater'.format(build_log['resource_type'].capitalize()))
            if build_log['resource_type']:
                template_key = 'templates/{0}.html'.format(build_log['resource_type'])
            else:
                template_key = 'templates/obs.html'  # Use a generic template here
        except AttributeError:
            templater_class = templaters.Templater
            template_key = 'templates/obs.html'  # Use a generic template here

        template_file = os.path.join(template_dir, 'template.html')
        print("Downloading {0} to {1}...".format(template_key, template_file))
        door43_handler.download_file(template_key, template_file)

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
                content += '<h1>{0}</h1>'.format(build_log['message'])
                content += '<p><i>No content is available to show for {0} yet.</i></p>'.format(repo_name)

            html = """
                <html lang="en">
                    <head>
                        <title>{0}</title>'

                    </head>
                    <body>
                        <div id="content">{1}</div>
                    </body>
                </html>""".format(repo_name, content)
            repo_index_file = os.path.join(source_dir, 'index.html')
            write_file(repo_index_file, html)

        # merge the source files with the template
        templater = templater_class(source_dir, output_dir, template_file)
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
                key = s3_commit_key + path.replace(output_dir, '')
                print("Uploading {0} to {1}".format(path, key))
                door43_handler.upload_file(path, key, 0)

        # Now we place json files and make an index.html file for the whole repo
        try:
            door43_handler.copy(from_key='{0}/project.json'.format(s3_repo_key), from_bucket=self.cdn_bucket)
            door43_handler.copy(from_key='{0}/manifest.json'.format(s3_commit_key), to_key='{0}/manifest.json'.format(s3_repo_key))
            door43_handler.redirect(s3_repo_key, '/' + s3_commit_key)
            door43_handler.redirect(s3_repo_key + '/index.html', '/' + s3_commit_key)

        except Exception:
            pass

        return True

    def redeploy_all_commits(self):
        cdn_handler = S3Handler(self.cdn_bucket)
        success = True
        for obj in cdn_handler.get_objects(prefix='u/', suffix='build_log.json'):
            success = (success and self.deploy_revision_to_door43(obj.key))
        return success

    @staticmethod
    def str_to_class(str):
        """
        Gets a class from a string.
        :param str|unicode str: The string of the class name
        """
        return reduce(getattr, str.split("."), sys.modules[__name__])


