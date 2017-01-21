import json
import os.path
import tempfile
import unittest
import zipfile

from general_tools import file_utils


class FileUtilsTest(unittest.TestCase):

    def test_unzip(self):
        tmp_dir = tempfile.mkdtemp()
        zip_file = tmp_dir + "/foo.zip"

        _, tmp_file = tempfile.mkstemp()
        with open(tmp_file, "w") as tmpf:
            tmpf.write("hello world")

        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.write(tmp_file, os.path.basename(tmp_file))

        file_utils.unzip(zip_file, tmp_dir)
        with open(os.path.join(tmp_dir, os.path.basename(tmp_file))) as outf:
            self.assertEqual(outf.read(), "hello world")

    def test_add_contents_to_zip(self):
        tmp_dir1 = tempfile.mkdtemp()
        zip_file = tmp_dir1 + "/foo.zip"

        tmp_dir2 = tempfile.mkdtemp()
        tmp_file = tmp_dir2 + "/foo.txt"
        with open(tmp_file, "w") as tmpf:
            tmpf.write("hello world")

        with zipfile.ZipFile(zip_file, "w"):
            pass  # create empty archive
        file_utils.add_contents_to_zip(zip_file, tmp_dir2)

        with zipfile.ZipFile(zip_file, "r") as zf:
            with zf.open(os.path.relpath(tmp_file, tmp_dir2), "r") as f:
                self.assertEqual(f.read().decode("ascii"), "hello world")

    def test_add_file_to_zip(self):
        tmp_dir1 = tempfile.mkdtemp()
        zip_file = tmp_dir1 + "/foo.zip"

        _, tmp_file = tempfile.mkstemp()
        with open(tmp_file, "w") as tmpf:
            tmpf.write("hello world")

        with zipfile.ZipFile(zip_file, "w"):
            pass  # create empty archive
        file_utils.add_file_to_zip(zip_file, tmp_file, os.path.basename(tmp_file))

        with zipfile.ZipFile(zip_file, "r") as zf:
            with zf.open(os.path.basename(tmp_file), "r") as f:
                self.assertEqual(f.read().decode("ascii"), "hello world")

    def test_make_dir(self):
        tmp_dir = tempfile.mkdtemp()
        sub_dir = tmp_dir + "/subdirectory"
        file_utils.make_dir(sub_dir)
        self.assertTrue(os.path.isdir(sub_dir))

    def test_load_json_object(self):
        d = {
            "one": 1,
            "two": 2,
            "child": {
                "three": 3
            }
        }
        _, tmp_file = tempfile.mkstemp()
        with open(tmp_file, "w") as tmpf:
            json.dump(d, tmpf)
        self.assertEqual(file_utils.load_json_object(tmp_file), d)

    def test_read_file(self):
        _, tmp_file = tempfile.mkstemp()
        with open(tmp_file, "w") as tmpf:
            tmpf.write("hello world")
        self.assertEqual(file_utils.read_file(tmp_file), "hello world")

    def test_write_file(self):
        _, tmp_file = tempfile.mkstemp()
        file_utils.write_file(tmp_file, "hello world")
        with open(tmp_file, "r") as f:
            self.assertEqual(f.read(), "hello world")

    def test_write_file_json(self):
        """
        A call to `write_file` where the content is an object (as opposed to a
        string).
        """
        d = {"one": 1, "two": 2, "child": {"numbers": [3, 4, 5]}}
        _, tmp_file = tempfile.mkstemp()
        file_utils.write_file(tmp_file, d)
        with open(tmp_file, "r") as f:
            self.assertEqual(json.load(f), d)

    def test_get_mime_type(self):
        tmp_dir = tempfile.mkdtemp()
        tmp_file = tmp_dir + "/hello.txt"
        with open(tmp_file, "w") as f:
            f.write("hello world")
        self.assertEqual(file_utils.get_mime_type(tmp_file), "text/plain")

    def test_get_files(self):
        tmp_dir = tempfile.mkdtemp()
        _, tmp_file1 = tempfile.mkstemp(dir=tmp_dir)
        _, tmp_file2 = tempfile.mkstemp(dir=tmp_dir)
        tmp_subdir = tmp_dir + "/subdir"
        os.mkdir(tmp_subdir)
        _, tmp_file3 = tempfile.mkstemp(dir=tmp_subdir)

        files = file_utils.get_files(tmp_dir, relative_paths=False, include_directories=True)
        self.assertEqual(len(files), 4)
        self.assertTrue(any(self.paths_equal(tmp_file1, d) for d in files))
        self.assertTrue(any(self.paths_equal(tmp_file2, d) for d in files))
        self.assertTrue(any(self.paths_equal(tmp_subdir, d) for d in files))
        self.assertTrue(any(self.paths_equal(tmp_file3, d) for d in files))

        files = file_utils.get_files(tmp_dir, relative_paths=True, include_directories=True)
        self.assertEqual(len(files), 4)
        self.assertTrue(any(self.paths_equal(os.path.relpath(tmp_file1, tmp_dir), d)
                            for d in files))
        self.assertTrue(any(self.paths_equal(os.path.relpath(tmp_file2, tmp_dir), d)
                            for d in files))
        self.assertTrue(any(self.paths_equal(os.path.relpath(tmp_subdir, tmp_dir), d)
                            for d in files))
        self.assertTrue(any(self.paths_equal(os.path.relpath(tmp_file3, tmp_dir), d)
                            for d in files))

    def test_get_subdirs(self):
        tmp_dir = tempfile.mkdtemp()
        _, tmp_file1 = tempfile.mkstemp(dir=tmp_dir)
        _, tmp_file2 = tempfile.mkstemp(dir=tmp_dir)
        tmp_subdir = tmp_dir + "/subdir"
        os.mkdir(tmp_subdir)
        tmp_subsubdir =tmp_subdir + "/subdir"
        os.mkdir(tmp_subsubdir)

        subdirs = file_utils.get_subdirs(tmp_dir, relative_paths=False)
        self.assertEqual(len(subdirs), 2)
        self.assertTrue(any(self.paths_equal(tmp_subdir, d) for d in subdirs))
        self.assertTrue(any(self.paths_equal(tmp_subsubdir, d) for d in subdirs))

        subdirs = file_utils.get_subdirs(tmp_dir, relative_paths=True)
        self.assertEqual(len(subdirs), 2)
        self.assertTrue(any(self.paths_equal("subdir", d) for d in subdirs))
        self.assertTrue(any(self.paths_equal("subdir/subdir/", d) for d in subdirs))

    @staticmethod
    def paths_equal(path1, path2):
        return os.path.normpath(path1) == os.path.normpath(path2)
