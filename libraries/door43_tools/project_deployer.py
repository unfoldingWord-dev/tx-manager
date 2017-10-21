from __future__ import print_function, unicode_literals
import os
import tempfile
import json
import time
from glob import glob
from shutil import copyfile

from libraries.general_tools import file_utils
from libraries.general_tools.file_utils import write_file, remove_tree
from libraries.door43_tools.templaters import init_template
from datetime import datetime, timedelta
from libraries.app.app import App


class ProjectDeployer(object):
    """
    Deploys a project's revision to the door43.org bucket

    Read from the project's user dir in the cdn.door43.org bucket
    by applying the door43.org template to the raw html files
    """

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(suffix="", prefix="deployer_")

    def close(self):
        """delete temp files"""
        remove_tree(self.temp_dir)

    def __del__(self):
        self.close()

    def deploy_revision_to_door43(self, build_log_key):
        """
        Deploys a single revision of a project to door43.org
        :param string build_log_key:
        :return bool:
        """
        build_log = None
        try:
            build_log = App.cdn_s3_handler().get_json(build_log_key, catch_exception=False)
        except Exception as e:
            App.logger.debug("Deploying error could not access {0}: {1}".format(build_log_key, str(e)))
            pass

        if not build_log or 'commit_id' not in build_log or 'repo_owner' not in build_log \
                or 'repo_name' not in build_log:
            App.logger.debug("Exiting, Invalid build log at {0}: {1}".format(build_log_key, build_log))
            return False

        start = time.time()
        App.logger.debug("Deploying, build log: " + json.dumps(build_log)[:256])

        user = build_log['repo_owner']
        repo_name = build_log['repo_name']
        commit_id = build_log['commit_id'][:10]

        s3_commit_key = 'u/{0}/{1}/{2}'.format(user, repo_name, commit_id)
        s3_repo_key = 'u/{0}/{1}'.format(user, repo_name)
        download_key = s3_commit_key

        partial_deploy = False
        multipart_merge = False
        if 'multiple' in build_log:
            multipart_merge = build_log['multiple']
            App.logger.debug("Found multi-part merge: {0}".format(download_key))

            prefix = download_key + '/'
            undeployed = self.get_undeployed_parts(prefix)
            if len(undeployed) > 0:
                App.logger.debug("Exiting, Parts not yet deployed: {0}".format(undeployed))
                return False

            key_deployed_ = download_key + '/deployed'
            if App.cdn_s3_handler().key_exists(key_deployed_):
                App.logger.debug("Exiting, Already merged parts: {0}".format(download_key))
                return False
            self.write_data_to_file(self.temp_dir, key_deployed_, 'deployed', ' ')  # flag that deploy has begun

        elif 'part' in build_log:
            part = build_log['part']
            download_key += '/' + part
            partial_deploy = True
            App.logger.debug("found partial: {0}".format(download_key))

            if not App.cdn_s3_handler().key_exists(download_key + '/finished'):
                App.logger.debug("Exiting, Not ready to process partial")
                return False

        source_dir = tempfile.mkdtemp(prefix='source_', dir=self.temp_dir)
        output_dir = tempfile.mkdtemp(prefix='output_', dir=self.temp_dir)
        template_dir = tempfile.mkdtemp(prefix='template_', dir=self.temp_dir)

        resource_type = build_log['resource_type']
        template_key = 'templates/project-page.html'
        template_file = os.path.join(template_dir, 'project-page.html')
        App.logger.debug("Downloading {0} to {1}...".format(template_key, template_file))
        App.door43_s3_handler().download_file(template_key, template_file)

        if not multipart_merge:
            source_dir, success = self.template_converted_files(build_log, download_key, output_dir, repo_name,
                                                                resource_type, s3_commit_key, source_dir, start,
                                                                template_file)
            if not success:
                return
        else:
            # merge multi-part project
            source_dir, success = self.multipart_master_merge(s3_commit_key, resource_type, download_key, output_dir,
                                                              source_dir, start, template_file)
            if not success:
                return False

        #######################
        #
        #  Now do the deploy
        #
        #######################

        # Copy first HTML file to index.html if index.html doesn't exist
        if not partial_deploy or multipart_merge:
            html_files = sorted(glob(os.path.join(output_dir, '*.html')))
            index_file = os.path.join(output_dir, 'index.html')
            if len(html_files) > 0 and not os.path.isfile(index_file):
                copyfile(os.path.join(output_dir, html_files[0]), index_file)

        # Copy all other files over that don't already exist in output_dir, like css files
        for filename in sorted(glob(os.path.join(source_dir, '*'))):
            output_file = os.path.join(output_dir, os.path.basename(filename))
            if not os.path.exists(output_file) and not os.path.isdir(filename):
                copyfile(filename, output_file)

            if partial_deploy:  # move files to common area
                basename = os.path.basename(filename)
                if basename not in ['finished', 'build_log.json', 'index.html', 'merged.json', 'lint_log.json']:
                    App.logger.debug("Moving {0} to common area".format(basename))
                    App.cdn_s3_handler().upload_file(filename, s3_commit_key + '/' + basename, cache_time=0)
                    App.cdn_s3_handler().delete_file(download_key + '/' + basename)

        # save master build_log.json
        file_utils.write_file(os.path.join(output_dir, 'build_log.json'), build_log)
        App.logger.debug("Final build_log.json:\n" + json.dumps(build_log)[:256])

        # Upload all files to the door43.org bucket
        for root, dirs, files in os.walk(output_dir):
            for f in sorted(files):
                path = os.path.join(root, f)
                if os.path.isdir(path):
                    continue
                key = s3_commit_key + path.replace(output_dir, '').replace(os.path.sep, '/')
                App.logger.debug("Uploading {0} to {1}".format(path, key))
                App.door43_s3_handler().upload_file(path, key, cache_time=0)

        if not partial_deploy:
            # Now we place json files and make an index.html file for the whole repo
            try:
                App.door43_s3_handler().copy(from_key='{0}/project.json'.format(s3_repo_key), from_bucket=App.cdn_bucket)
                App.door43_s3_handler().copy(from_key='{0}/manifest.json'.format(s3_commit_key),
                                             to_key='{0}/manifest.json'.format(s3_repo_key))
                App.door43_s3_handler().redirect(s3_repo_key, '/' + s3_commit_key)
                App.door43_s3_handler().redirect(s3_repo_key + '/index.html', '/' + s3_commit_key)
                self.write_data_to_file(output_dir, s3_commit_key, 'deployed', ' ')  # flag that deploy has finished
            except:
                pass

        else:  # if processing part of multi-part merge
            self.write_data_to_file(output_dir, download_key, 'deployed', ' ')  # flag that deploy has finished
            if App.cdn_s3_handler().key_exists(s3_commit_key + '/final_build_log.json'):
                App.logger.debug("final build detected")
                App.logger.debug("conversions all finished, trigger final merge")
                App.cdn_s3_handler().copy(from_key=s3_commit_key + '/final_build_log.json',
                                          to_key=s3_commit_key + '/build_log.json')

        elapsed_seconds = int(time.time() - start)
        App.logger.debug("deploy type partial={0}, multi_merge={1}".format(partial_deploy, multipart_merge))
        App.logger.debug("deploy completed in {0} seconds".format(elapsed_seconds))
        self.close()
        return True

    def multipart_master_merge(self, s3_commit_key, resource_type, download_key, output_dir, source_dir, start,
                               template_file):
        prefix = download_key + '/'
        App.door43_s3_handler().download_dir(prefix, source_dir)  # get previous templated files
        source_dir = os.path.join(source_dir, download_key)
        files = sorted(glob(os.path.join(source_dir, '*.*')))
        for f in files:
            App.logger.debug("Downloaded: " + f)
        fname = os.path.join(source_dir, 'index.html')
        if os.path.isfile(fname):
            os.remove(fname)  # remove index if already exists
        elapsed_seconds = int(time.time() - start)
        App.logger.debug("deploy download completed in " + str(elapsed_seconds) + " seconds")
        templater = init_template(resource_type, source_dir, output_dir, template_file)
        # restore index from previous passes
        index_json = self.get_templater_index(s3_commit_key, 'index.json')
        templater.titles = index_json['titles']
        templater.chapters = index_json['chapters']
        templater.book_codes = index_json['book_codes']
        templater.already_converted = templater.files  # do not reconvert files
        # merge the source files with the template
        try:
            self.run_templater(templater)
            success = True
        except Exception as e:
            App.logger.error("Error multi-part applying template {0} to resource type {1}".format(template_file,
                                                                                                  resource_type))
            self.close()
            success = False
        return source_dir, success

    def get_undeployed_parts(self, prefix):
        unfinished = []
        for o in App.cdn_s3_handler().get_objects(prefix=prefix, suffix='/build_log.json'):
            parts = o.key.split(prefix)
            if len(parts) == 2:
                parts = parts[1].split('/')
                if len(parts) > 1:
                    part_num = parts[0]
                    deployed_key = prefix + part_num + '/deployed'
                    if not App.cdn_s3_handler().key_exists(deployed_key):
                        App.logger.debug("Part {0} unfinished".format(part_num))
                        unfinished.append(part_num)
        return unfinished

    def template_converted_files(self, build_log, download_key, output_dir, repo_name, resource_type, s3_commit_key,
                                 source_dir, start, template_file):
        App.cdn_s3_handler().download_dir(download_key + '/', source_dir)
        source_dir = os.path.join(source_dir, download_key)
        elapsed_seconds = int(time.time() - start)
        App.logger.debug("deploy download completed in " + str(elapsed_seconds) + " seconds")
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
            else:
                content += '<h1 class="conversion-requested">{0}</h1>'.format(build_log['message'])
                content += '<p><i>No content is available to show for {0} yet.</i></p>'.format(repo_name)
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

        # merge the source files with the template
        templater = init_template(resource_type, source_dir, output_dir, template_file)
        try:
            self.run_templater(templater)
            success = True
        except Exception as e:
            App.logger.error("Error applying template {0} to resource type {1}".format(template_file,
                                                                                       resource_type))
            self.close()
            success = False

        if success:
            # update index of templated files
            index_json_fname = 'index.json'
            index_json = self.get_templater_index(s3_commit_key, index_json_fname)
            App.logger.debug("initial 'index.json': " + json.dumps(index_json)[:256])
            self.update_index_key(index_json, templater, 'titles')
            self.update_index_key(index_json, templater, 'chapters')
            self.update_index_key(index_json, templater, 'book_codes')
            App.logger.debug("final 'index.json': " + json.dumps(index_json)[:256])
            self.write_data_to_file(output_dir, s3_commit_key, index_json_fname, index_json)
        return source_dir, success

    def write_data_to_file(self, output_dir, s3_commit_key, fname, data):
        out_file = os.path.join(output_dir, fname)
        write_file(out_file, data)
        key = s3_commit_key + '/' + fname
        App.logger.debug("Writing {0} to {1}': ".format(fname, key))
        App.cdn_s3_handler().upload_file(out_file, key, cache_time=0)

    def run_templater(self, templater):  # for test purposes
        templater.run()

    @staticmethod
    def update_index_key(index_json, templater, key):
        data = index_json[key]
        data.update(getattr(templater, key))
        index_json[key] = data

    @staticmethod
    def get_templater_index(s3_commit_key, index_json_fname):
        index_json = App.cdn_s3_handler().get_json(s3_commit_key + '/' + index_json_fname)
        if not index_json:
            index_json['titles'] = {}
            index_json['chapters'] = {}
            index_json['book_codes'] = {}
        return index_json

    @staticmethod
    def redeploy_all_projects(deploy_function):
        i = 0
        one_day_ago = datetime.utcnow() - timedelta(hours=24)
        for obj in App.cdn_s3_handler().get_objects(prefix='u/', suffix='build_log.json'):
            i += 1
            last_modified = obj.last_modified.replace(tzinfo=None)
            if one_day_ago <= last_modified:
                continue
            App.lambda_handler().invoke(
                FunctionName=deploy_function,
                InvocationType='Event',
                LogType='Tail',
                Payload=json.dumps({
                    'prefix': App.prefix,
                    'build_log_key': obj.key
                })
            )
        return True
