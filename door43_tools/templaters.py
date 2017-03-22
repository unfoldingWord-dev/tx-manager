from __future__ import unicode_literals, print_function
import os
import json
import codecs
from glob import glob
from bs4 import BeautifulSoup
from general_tools.file_utils import write_file
from door43_tools.manifest_handler import Manifest


class Templater(object):
    def __init__(self, source_dir, output_dir, template_file, quiet=False):
        self.source_dir = source_dir  # Local directory
        self.output_dir = output_dir  # Local directory
        self.template_file = template_file  # Local file of template
        self.quiet = quiet

        self.files = sorted(glob(os.path.join(self.source_dir, '*.html')))
        self.manifest = None
        self.build_log = {}
        self.template_html = ''

    def run(self):
        repo_name = ""

        print(glob(os.path.join(self.source_dir, '*')))

        # get build_log
        build_log_filename = os.path.join(self.source_dir, 'build_log.json')
        if os.path.isfile(build_log_filename):
            with open(build_log_filename) as build_log_file:
                self.build_log = json.load(build_log_file)
                repo_name = self.build_log['repo_name']

        # get manifest
        manifest_filename = os.path.join(self.source_dir, 'manifest.json')
        self.manifest = Manifest(file_name=manifest_filename, repo_name=repo_name, files_path=self.source_dir)

        with open(self.template_file) as template_file:
            self.template_html = template_file.read()

        self.apply_template()

    def build_left_sidebar(self):
        html = self.build_page_nav()
        html += '<div><h1>Revisions</h1><table width="100%" id="revisions"></table></div>'
        return html

    def build_page_nav(self):
        html = '<select id="page-nav" onchange="window.location.href=this.value">'
        for filename in self.files:
            name = os.path.splitext(os.path.basename(filename))[0]
            html += '<option value="{0}">{1}</option>'.format(os.path.basename(filename), name)
        html += '</select>'
        return html

    def apply_template(self):
        language_code = self.manifest.target_language['id']
        language_name = self.manifest.target_language['name']
        resource_name = self.manifest.resource['name']

        heading = '{0}: {1}'.format(language_name, resource_name)
        title = ''
        canonical = ''

        # apply the template
        template = BeautifulSoup(self.template_html, 'html.parser')

        # find the target div in the template
        content_div = template.body.find('div', {'id': 'content'})
        if not content_div:
            raise Exception('No div tag with id "content" was found in the template')

        left_sidebar_div = template.body.find('div', {'id': 'left-sidebar'})
        if left_sidebar_div:
            left_sidebar_html = '<span>'+self.build_left_sidebar()+'</span>'
            left_sidebar_soup = BeautifulSoup(left_sidebar_html, 'html.parser')
            left_sidebar_div.clear()
            left_sidebar_div.append(left_sidebar_soup.span)

        # loop through the html files
        for filename in self.files:
            if not self.quiet:
                print('Applying template to {0}.'.format(filename))

            # read the downloaded file into a dom abject
            with codecs.open(filename, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f, 'html.parser')

            # get the language code, if we haven't yet
            if not language_code:
                if 'lang' in soup.html:
                    language_code = soup.html['lang']
                else:
                    language_code = 'en'

            # get the title, if we haven't
            if not title and soup.head and soup.head.title:
                title = soup.head.title.text
            else:
                title = os.path.basename(filename)

            # get the canonical UTL, if we haven't
            if not canonical:
                links = template.head.select('link[rel="canonical"]')
                if len(links) == 1:
                    canonical = links[0]['href']

            if soup.body:
                body = soup.body
            else:
                body = soup

            # get the content div from the temp file
            soup_content = body.find('div', {'id': 'content'})
            if not soup_content:
                soup_content = body

            # insert new HTML into the template
            content_div.clear()
            content_div.append(soup_content)
            template.html['lang'] = language_code
            template.head.title.clear()
            template.head.title.append(heading+' - '+title)
            try:
                for a_tag in template.body.select('a[rel="dct:source"]'):
                    a_tag.clear()
                    a_tag.append(title)
            except:
                pass

            # set the page heading
            heading_span = template.body.find('span', {'id': 'h1'})
            heading_span.clear()
            heading_span.append(heading)

            # get the html
            html = unicode(template)

            # update the canonical URL - it is in several different locations
            html = html.replace(canonical, canonical.replace('/templates/', '/{0}/'.format(language_code)))

            # write to output directory
            out_file = os.path.join(self.output_dir, os.path.basename(filename))

            if not self.quiet:
                print('Writing {0}.'.format(out_file))

            write_file(out_file, html.encode('ascii', 'xmlcharrefreplace'))


class ObsTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(ObsTemplater, self).__init__(*args, **kwargs)


class BibleTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(BibleTemplater, self).__init__(*args, **kwargs)
