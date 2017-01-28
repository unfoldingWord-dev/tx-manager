import os
import tempfile
import unittest
import json
import urllib
import shutil
from glob import glob

from door43_tools.templaters import Templater
from general_tools import file_utils

class TestTemplater(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """
        Runs before each test
        """
        self.out_dir = ''
        self.temp_dir = ""

    def tearDown(self):
        """
        Runs after each test
        """
        # delete temp files
        if os.path.isdir(self.out_dir):
            shutil.rmtree(self.out_dir, ignore_errors=True)
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def testTemplaterComplete(self):
        # given
        test_folder_name = "aab_obs_text_obs-complete"
        expect_success = True

        # when
        deployer, success = self.doTemplater(test_folder_name)

        # then
        self.verifyTemplater(success, expect_success, deployer.output_dir)


    def testCommitToDoor43Empty(self):
        # given
        test_folder_name = "aae_obs_text_obs-empty"
        expect_success = True
        missing_chapters = range(1, 51)

        # when
        deployer, success = self.doTemplater(test_folder_name)

        # then
        self.verifyTemplater(success, expect_success, deployer.output_dir, missing_chapters)


    def testCommitToDoor43MissingFirstFrame(self):
        # given
        test_folder_name = "aah_obs_text_obs-missing_first_frame"
        expect_success = True

        # when
        deployer, success = self.doTemplater(test_folder_name)

        # then
        self.verifyTemplater(success, expect_success, deployer.output_dir)


    def testCommitToDoor43MissingChapter50(self):
        # given
        test_folder_name = "aai_obs_text_obs-missing_chapter_50"
        expect_success = True
        missing_chapters = [50]

        # when
        deployer, success = self.doTemplater(test_folder_name)

        # then
        self.verifyTemplater(success, expect_success, deployer.output_dir, missing_chapters)


    # empty
    # <div class="col-md-3 sidebar" id="left-sidebar" role="complementary"><span><select id="page-nav" onchange="window.location.href=this.value"><option value="all.html">all</option></select><div><h1>Revisions</h1><table id="revisions" width="100%"></table></div></span></div>

    # <div class="col-md-3 sidebar" id="left-sidebar" role="complementary"><span><select id="page-nav" onchange="window.location.href=this.value"><option value="01.html">01</option><option value="02.html">02</option><option value="03.html">03</option><option value="04.html">04</option><option value="05.html">05</option><option value="06.html">06</option><option value="07.html">07</option><option value="08.html">08</option><option value="09.html">09</option><option value="10.html">10</option><option value="11.html">11</option><option value="12.html">12</option><option value="13.html">13</option><option value="14.html">14</option><option value="15.html">15</option><option value="16.html">16</option><option value="17.html">17</option><option value="18.html">18</option><option value="19.html">19</option><option value="20.html">20</option><option value="21.html">21</option><option value="22.html">22</option><option value="23.html">23</option><option value="24.html">24</option><option value="25.html">25</option><option value="26.html">26</option><option value="27.html">27</option><option value="28.html">28</option><option value="29.html">29</option><option value="30.html">30</option><option value="31.html">31</option><option value="32.html">32</option><option value="33.html">33</option><option value="34.html">34</option><option value="35.html">35</option><option value="36.html">36</option><option value="37.html">37</option><option value="38.html">38</option><option value="39.html">39</option><option value="40.html">40</option><option value="41.html">41</option><option value="42.html">42</option><option value="43.html">43</option><option value="44.html">44</option><option value="45.html">45</option><option value="46.html">46</option><option value="47.html">47</option><option value="48.html">48</option><option value="49.html">49</option><option value="all.html">all</option><option value="front.html">front</option><option value="hide.50.html">hide.50</option></select><div><h1>Revisions</h1><table id="revisions" width="100%"></table></div></span></div>

    def doTemplater(self, test_folder_name):
        source_dir = os.path.join(self.resources_dir, test_folder_name)
        template_file = os.path.join(self.resources_dir, 'templates/obs.html')
        self.out_dir = tempfile.mkdtemp(prefix='output_')
        success = True
        templater = Templater(source_dir, self.out_dir, template_file)
        try:
            templater.run()
        except Exception as e:
            print("Templater threw exception: " + e)
            success = False

        return templater, success

    def verifyTemplater(self, success, expect_success, output_folder, missing_chapters = []):
        self.assertIsNotNone(output_folder)
        self.assertEqual(success, expect_success)

        files_to_verify = []
        files_missing = []
        for i in range(1, 51):
            file_name = str(i).zfill(2) + '.html'
            files_to_verify.append(file_name)

        for file_to_verify in files_to_verify:
            file_name = os.path.join(output_folder, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'file not found: {0}'.format(file_name))

        for file_to_verify in files_missing:
            file_name = os.path.join(output_folder, file_to_verify)
            self.assertFalse(os.path.isfile(file_name), 'file present, but should not be: {0}'.format(file_name))



if __name__ == '__main__':
    unittest.main()
