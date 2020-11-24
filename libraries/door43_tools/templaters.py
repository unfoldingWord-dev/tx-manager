from __future__ import unicode_literals, print_function
import os
import codecs
import sys
import bs4
from glob import glob
from bs4 import BeautifulSoup
from libraries.general_tools import file_utils
from libraries.general_tools.file_utils import write_file
from libraries.resource_container.ResourceContainer import RC
from libraries.general_tools.file_utils import load_yaml_object
from libraries.app.app import App


def do_template(resource_type, source_dir, output_dir, template_file):
    templater = init_template(resource_type, source_dir, output_dir, template_file)
    return templater.run()


def init_template(resource_type, source_dir, output_dir, template_file):
    if resource_type == 'obs':
        templater = ObsTemplater(resource_type, source_dir, output_dir, template_file)
    elif resource_type == 'ta':
        templater = TaTemplater(resource_type, source_dir, output_dir, template_file)
    elif resource_type == 'tq':
        templater = TqTemplater(resource_type, source_dir, output_dir, template_file)
    elif resource_type == 'tw':
        templater = TwTemplater(resource_type, source_dir, output_dir, template_file)
    elif resource_type == 'tn':
        templater = TnTemplater(resource_type, source_dir, output_dir, template_file)
    else:
        templater = BibleTemplater(resource_type, source_dir, output_dir, template_file)
    return templater


class Templater(object):
    NO_NAV_TITLES = ['', 'Conversion requested...', 'Conversion started...', 'Conversion successful',
                     'Conversion successful with warnings', 'Index']

    def __init__(self, resource_type, source_dir, output_dir, template_file):
        self.resource_type = resource_type
        self.source_dir = source_dir  # Local directory
        self.output_dir = output_dir  # Local directory
        self.template_file = template_file  # Local file of template

        self.files = sorted(glob(os.path.join(self.source_dir, '*.html')))
        self.rc = None
        self.template_html = ''
        self.already_converted = []
        self.titles = {}
        self.chapters = {}
        self.book_codes = {}
        self.classes = []

    def run(self):
        # get the resource container
        self.rc = RC(self.source_dir)
        with open(self.template_file) as template_file:
            self.template_html = template_file.read()
            soup = BeautifulSoup(self.template_html, 'html.parser')
            soup.body['class'] = soup.body.get('class', []) + [self.resource_type]
            if self.classes:
                soup.body['class'] = soup.body.get('class', []) + self.classes
            self.template_html = unicode(soup)
        self.apply_template()
        return True

    @staticmethod
    def build_left_sidebar(filename=None):
        html = """
            <nav class="affix-top hidden-print hidden-xs hidden-sm" id="left-sidebar-nav">
                <div class="nav nav-stacked" id="revisions-div">
                    <h1>Revisions</h1>
                    <table width="100%" id="revisions"></table>
                </div>
            </nav>
            """
        return html

    def build_right_sidebar(self, filename=None):
        html = self.build_page_nav(filename)
        return html

    def build_page_nav(self, filename=None):
        html = """
            <nav class="affix-top hidden-print hidden-xs hidden-sm content-nav" id="right-sidebar-nav">
              <ul id="sidebar-nav" class="nav nav-stacked">
                <li><h1>Navigation</h1></li>
            """
        for fname in self.files:
            key = os.path.basename(fname)
            title = ""
            if key in self.titles:
                title = self.titles[key]
            if title in self.NO_NAV_TITLES:
                continue
            if filename != fname:
                html += '<li><a href="{0}">{1}</a></li>'.format(os.path.basename(fname), title)
            else:
                html += '<li>{0}</li>'.format(title)
        html += """
                </ul>
            </nav>
            """
        return html

    def get_page_navigation(self):
        for fname in self.files:
            key = os.path.basename(fname)
            if key in self.titles:  # skip if we already have data
                continue

            with codecs.open(fname, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f, 'html.parser')
            if soup.select('div#content h1'):
                title = soup.select('div#content h1')[0].text.strip() 
            else:
                title = os.path.splitext(os.path.basename(fname))[0].replace('_', ' ').capitalize()

            self.titles[key] = title

    def apply_template(self):

        App.logger.debug('bs4 version: ' + bs4.__version__)
        sys.setrecursionlimit(3000)
        App.logger.debug('Recursion limit: ' + str(sys.getrecursionlimit()))

        language_code = self.rc.resource.language.identifier
        language_name = self.rc.resource.language.title
        language_dir = self.rc.resource.language.direction
        resource_title = self.rc.resource.title

        self.get_page_navigation()

        heading = '{0}: {1}'.format(language_name, resource_title)
        title = ''
        canonical = ''

        # soup is the template that we will replace content of for every file
        soup = BeautifulSoup(self.template_html, 'html.parser')
        left_sidebar_div = soup.body.find('div', id='left-sidebar')
        outer_content_div = soup.body.find('div', id='outer-content')
        right_sidebar_div = soup.body.find('div', id='right-sidebar')

        # find the outer-content div in the template
        if not outer_content_div:
            raise Exception('No div tag with id "outer-content" was found in the template')

        # get the canonical UTL
        if not canonical:
            links = soup.head.find_all('link[rel="canonical"]')
            if len(links) == 1:
                canonical = links[0]['href']

        # loop through the html files
        for filename in self.files:
            if filename not in self.already_converted:
                App.logger.debug('Applying template to {0}.'.format(filename))

                # read the downloaded file into a dom abject
                with codecs.open(filename, 'r', 'utf-8-sig') as f:
                    file_soup = BeautifulSoup(f, 'html.parser')

                # get the title from the raw html file
                if not title and file_soup.head and file_soup.head.title:
                    title = file_soup.head.title.text
                else:
                    title = os.path.basename(filename)

                # get the language code, if we haven't yet
                if not language_code:
                    if 'lang' in file_soup.html:
                        language_code = file_soup.html['lang']
                    else:
                        language_code = 'en'

                # get the body of the raw html file
                if not file_soup.body:
                    body = BeautifulSoup('<div>No content</div>', 'html.parser')
                else:
                    body = BeautifulSoup(''.join(['%s' % x for x in file_soup.body.contents]), 'html.parser')

                # insert new HTML into the template
                outer_content_div.clear()
                outer_content_div.append(body)
                soup.html['lang'] = language_code
                soup.html['dir'] = language_dir

                soup.head.title.clear()
                soup.head.title.append(heading+' - '+title)

                # set the page heading
                heading_span = soup.body.find('span', id='h1')
                heading_span.clear()
                heading_span.append(heading)

                if left_sidebar_div:
                    left_sidebar_html = self.build_left_sidebar(filename)
                    left_sidebar = BeautifulSoup(left_sidebar_html, 'html.parser').nav.extract()
                    left_sidebar_div.clear()
                    left_sidebar_div.append(left_sidebar)

                if right_sidebar_div:
                    right_sidebar_div.clear()
                    right_sidebar_html = self.build_right_sidebar(filename)
                    if right_sidebar_html:
                        right_sidebar = BeautifulSoup(right_sidebar_html, 'html.parser')
                        if right_sidebar and right_sidebar.nav:
                            right_sidebar_nav = right_sidebar.nav.extract()
                            right_sidebar_div.append(right_sidebar_nav)

                # render the html as an unicode string
                html = unicode(soup)

                # fix the footer message, removing the title of this page in parentheses as it doesn't get filled
                html = html.replace(
                    '("<a xmlns:dct="http://purl.org/dc/terms/" href="https://live.door43.org/templates/project-page.html" rel="dct:source">{{ HEADING }}</a>") ',
                    '')
                # update the canonical URL - it is in several different locations
                html = html.replace(canonical, canonical.replace('/templates/', '/{0}/'.format(language_code)))

                # Replace HEADING with page title in footer
                html = html.replace('{{ HEADING }}', title)

                # write to output directory
                out_file = os.path.join(self.output_dir, os.path.basename(filename))
                App.logger.debug('Writing {0}.'.format(out_file))
                write_file(out_file, html.encode('ascii', 'xmlcharrefreplace'))

            else:  # if already templated, need to update navigation bar
                # read the templated file into a dom abject
                with codecs.open(filename, 'r', 'utf-8-sig') as f:
                    soup = BeautifulSoup(f, 'html.parser')

                right_sidebar_div = soup.body.find('div', id='right-sidebar')
                if right_sidebar_div:
                    right_sidebar_html = self.build_right_sidebar(filename)
                    right_sidebar = BeautifulSoup(right_sidebar_html, 'html.parser').nav.extract()
                    right_sidebar_div.clear()
                    right_sidebar_div.append(right_sidebar)

                    # render the html as an unicode string
                    html = unicode(soup)

                    # write to output directory
                    out_file = os.path.join(self.output_dir, os.path.basename(filename))
                    App.logger.debug('Updating nav in {0}.'.format(out_file))
                    write_file(out_file, html.encode('ascii', 'xmlcharrefreplace'))


class ObsTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(ObsTemplater, self).__init__(*args, **kwargs)


class TqTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(TqTemplater, self).__init__(*args, **kwargs)
        index = file_utils.load_json_object(os.path.join(self.source_dir, 'index.json'))
        if index:
            self.titles = index['titles']
            self.chapters = index['chapters']
            self.book_codes = index['book_codes']

    def get_page_navigation(self):
        for fname in self.files:
            key = os.path.basename(fname)
            if key in self.titles:  # skip if we already have data
                continue
            filebase = os.path.splitext(os.path.basename(fname))[0]
            # Getting the book code for HTML tag references
            fileparts = filebase.split('-')
            if len(fileparts) == 2:
                # Assuming filename of ##-<name>.usfm, such as 01-GEN.usfm
                book_code = fileparts[1].lower()
            else:
                # Assuming filename of <name.usfm, such as GEN.usfm
                book_code = fileparts[0].lower()
            book_code.replace(' ', '-').replace('.', '-')  # replacing spaces and periods since used as tag class
            with codecs.open(fname, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            if soup.select('div#content h1'):
                title = soup.select('div#content h1')[0].text.strip() 
            else:
                title = '{0}.'.format(book_code)
            self.titles[key] = title
            self.book_codes[key] = book_code
            chapters = soup.find_all('h2')
            self.chapters[key] = [c['id'] for c in chapters]

    def build_page_nav(self, filename=None):
        html = """
        <nav class="hidden-print hidden-xs hidden-sm content-nav" id="right-sidebar-nav">
            <ul id="sidebar-nav" class="nav nav-stacked books panel-group">
            """
        for fname in self.files:
            key = os.path.basename(fname)
            book_code = ""
            if key in self.book_codes:
                book_code = self.book_codes[key]
            title = ""
            if key in self.titles:
                title = self.titles[key]
            if title in self.NO_NAV_TITLES:
                continue
            html += """
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a class="accordion-toggle" data-toggle="collapse" data-parent="#sidebar-nav" href="#collapse{0}">{1}</a>
                        </h4>
                    </div>
                    <div id="collapse{0}" class="panel-collapse collapse{2}">
                        <ul class="panel-body chapters">
                    """.format(book_code, title, ' in' if fname == filename else '')
            chapters = {}
            if key in self.chapters:
                chapters = self.chapters[key]
            for chapter in chapters:
                chapter_parts = chapter.split('-')
                label = chapter if len(chapter_parts) < 4 else chapter_parts[3].lstrip('0')
                html += """
                       <li class="chapter"><a href="{0}#{1}">{2}</a></li>
                    """.format(os.path.basename(fname) if fname != filename else '', chapter,
                               label)
            html += """
                        </ul>
                    </div>
                </div>
                    """
        html += """
            </ul>
        </nav>
            """
        return html


class TwTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(TwTemplater, self).__init__(*args, **kwargs)
        index = file_utils.load_json_object(os.path.join(self.source_dir, 'index.json'))
        if index:
            self.titles = index['titles']
            self.chapters = index['chapters']

    def build_page_nav(self, filename=None):
        if not self.files or not self.titles or not self.chapters:
            return ""
        html = """
            <nav class="hidden-print hidden-xs hidden-sm content-nav" id="right-sidebar-nav">
                <ul class="nav nav-stacked">
        """
        for fname in self.files:
            key = os.path.basename(fname)
            section = os.path.splitext(key)[0]
            html += """
                    <li{0}><a href="{1}#tw-section-{2}">{3}</a>
                        <a class="content-nav-expand collapsed" data-target="#section-{2}-sub" data-toggle="collapse" href="#"></a>
                        <ul class="collapse" id="section-{2}-sub">
            """.format(' class="active"' if fname == filename else '', key if fname != filename else '',
                       section, self.titles[key])
            titles = self.chapters[key]
            terms_sorted_by_title = sorted(titles, key=lambda i: titles[i].lower())
            for term in terms_sorted_by_title:
                html += """
                            <li><a href="{0}#{1}">{2}</a></li>
                """.format(key if fname != filename else '', term, titles[term])
            html += """
                        </ul>
                    </li>
            """
        html += """
                </ul>
            </nav>
        """
        return html


class TnTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(TnTemplater, self).__init__(*args, **kwargs)
        index = file_utils.load_json_object(os.path.join(self.source_dir, 'index.json'))
        if index:
            self.titles = index['titles']
            self.chapters = index['chapters']
            self.book_codes = index['book_codes']

    def get_page_navigation(self):
        for fname in self.files:
            key = os.path.basename(fname)
            if key in self.titles:  # skip if we already have data
                continue
            filebase = os.path.splitext(os.path.basename(fname))[0]
            # Getting the book code for HTML tag references
            fileparts = filebase.split('-')
            if len(fileparts) == 2:
                # Assuming filename of ##-<name>.usfm, such as 01-GEN.usfm
                book_code = fileparts[1].lower()
            else:
                # Assuming filename of <name.usfm, such as GEN.usfm
                book_code = fileparts[0].lower()
            book_code.replace(' ', '-').replace('.', '-')  # replacing spaces and periods since used as tag class
            with codecs.open(fname, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            if soup.select('div#content h1'):
                title = soup.select('div#content h1')[0].text.strip()
            else:
                title = '{0}.'.format(book_code)
            self.titles[key] = title
            self.book_codes[key] = book_code
            chapters = soup.find_all('h2')
            self.chapters[key] = [c['id'] for c in chapters]

    def build_page_nav(self, filename=None):
        html = """
        <nav class="hidden-print hidden-xs hidden-sm content-nav" id="right-sidebar-nav">
            <ul id="sidebar-nav" class="nav nav-stacked books panel-group">
            """
        for fname in self.files:
            key = os.path.basename(fname)
            book_code = ""
            if key in self.book_codes:
                book_code = self.book_codes[key]
            title = ""
            if key in self.titles:
                title = self.titles[key]
            if title in self.NO_NAV_TITLES:
                continue
            html += """
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a class="accordion-toggle" data-toggle="collapse" data-parent="#sidebar-nav" href="#collapse{0}">{1}</a>
                        </h4>
                    </div>
                    <div id="collapse{0}" class="panel-collapse collapse{2}">
                        <ul class="panel-body chapters">
                    """.format(book_code, title, ' in' if fname == filename else '')
            chapters = {}
            if key in self.chapters:
                chapters = self.chapters[key]
            for chapter in chapters:
                chapter_parts = chapter.split('-')
                label = chapter if len(chapter_parts) < 4 else chapter_parts[3].lstrip('0')
                html += """
                       <li class="chapter"><a href="{0}#{1}">{2}</a></li>
                    """.format(os.path.basename(fname) if fname != filename else '', chapter,
                               label)
            html += """
                        </ul>
                    </div>
                </div>
                    """
        html += """
            </ul>
        </nav>
            """
        return html


class BibleTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(BibleTemplater, self).__init__(*args, **kwargs)
        self.classes = ['bible']

    def get_page_navigation(self):
        for fname in self.files:
            key = os.path.basename(fname)
            if key in self.titles:  # skip if we already have data
                continue
            filebase = os.path.splitext(os.path.basename(fname))[0]
            # Getting the book code for HTML tag references
            fileparts = filebase.split('-')
            if len(fileparts) == 2:
                # Assuming filename of ##-<name>.usfm, such as 01-GEN.usfm
                book_code = fileparts[1].lower()
            else:
                # Assuming filename of <name.usfm, such as GEN.usfm
                book_code = fileparts[0].lower()
            book_code.replace(' ', '-').replace('.', '-')  # replacing spaces and periods since used as tag class
            with codecs.open(fname, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            if soup.select('div#content h1'):
                title = soup.select('div#content h1')[0].text.strip() 
            else:
                title = '{0}.'.format(book_code)
            self.titles[key] = title
            self.book_codes[key] = book_code
            chapters = soup.find_all('h2', {'c-num'})
            self.chapters[key] = [c['id'] for c in chapters]

    def build_page_nav(self, filename=None):
        html = """
        <nav class="hidden-print hidden-xs hidden-sm content-nav" id="right-sidebar-nav">
            <ul id="sidebar-nav" class="nav nav-stacked books panel-group">
            """
        for fname in self.files:
            key = os.path.basename(fname)
            book_code = ""
            if key in self.book_codes:
                book_code = self.book_codes[key]
            title = ""
            if key in self.titles:
                title = self.titles[key]
            if title in self.NO_NAV_TITLES:
                continue
            html += """
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h4 class="panel-title">
                            <a class="accordion-toggle" data-toggle="collapse" data-parent="#sidebar-nav" href="#collapse{0}">{1}</a>
                        </h4>
                    </div>
                    <div id="collapse{0}" class="panel-collapse collapse{2}">
                        <ul class="panel-body chapters">
                    """.format(book_code, title, ' in' if fname == filename else '')

            chapters = {}
            if key in self.chapters:
                chapters = self.chapters[key]

            for chapter in chapters:
                chapter_parts = chapter.split('-')
                label = chapter if len(chapter_parts) < 3 else chapter_parts[2].lstrip('0')
                html += """
                       <li class="chapter"><a href="{0}#{1}">{2}</a></li>
                    """.format(os.path.basename(fname) if fname != filename else '', chapter,
                               label)
            html += """
                        </ul>
                    </div>
                </div>
                    """
        html += """
            </ul>
        </nav>
            """
        return html


class TaTemplater(Templater):
    def __init__(self, *args, **kwargs):
        super(TaTemplater, self).__init__(*args, **kwargs)
        self.section_container_id = 1

    def build_section_toc(self, section):
        """
        Recursive section toc builder
        :param dict section: 
        :return: 
        """
        if 'link' in section:
            link = section['link']
        else:
            link = 'section-container-{0}'.format(self.section_container_id)
            self.section_container_id = self.section_container_id + 1
        html = """
            <li>
                <a href="#{0}">{1}</a>
            """.format(link, section['title'])
        if 'sections' in section:
            html += """ 
                <a href="#" data-target="#{0}-sub" data-toggle="collapse" class="content-nav-expand collapsed"></a>
                <ul id="{0}-sub" class="collapse">
            """.format(link)
            for subsection in section['sections']:
                html += self.build_section_toc(subsection)
            html += """
                </ul>
            """
        html += """
            </li>
        """
        return html

    def build_page_nav(self, filename=None):
        self.section_container_id = 1
        html = """
            <nav class="hidden-print hidden-xs hidden-sm content-nav" id="right-sidebar-nav">
                <ul class="nav nav-stacked">
        """
        for fname in self.files:
            with codecs.open(fname, 'r', 'utf-8-sig') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            if soup.select('div#content h1'):
                title = soup.select('div#content h1')[0].text.strip() 
            else:
                title = os.path.splitext(os.path.basename(fname))[0].title()
            if title in self.NO_NAV_TITLES:
                continue
            if fname != filename:
                html += """
                <h4><a href="{0}">{1}</a></h4>
                """.format(os.path.basename(fname), title)
            else:
                html += """
                <h4>{0}</h4>
                """.format(title)
                toc = load_yaml_object(os.path.join('{0}-toc.yaml'.format(os.path.splitext(fname)[0])))
                if toc:
                    for section in toc['sections']:
                        html += self.build_section_toc(section)
                html += """
                """
        html += """
                </ul>
            </nav>
        """
        return html
