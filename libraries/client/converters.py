import os
import json
import re
from libraries.app.app import App


def txt2md(rootdir="."):
    """
    Converts txt files to markdown
    """
    proccessed = False
    for dir, subdir, files in os.walk(rootdir):
        for fname in files:
            filepath = os.path.join(dir, fname)
            fileinfo = os.path.splitext(fname)

            filename = fileinfo[0]
            ext = fileinfo[1]

            App.logger.debug('Filepath: {0}'.format(filepath))

            if ext == ".txt":
                with open(filepath, "r") as data_file:
                    # if content of the file starts from the valid json character
                    # then it's a json file
                    if re.match(r"^\[|^\{", data_file.read()):
                        try:
                            data = json.load(data_file)
                            md = ""
                            for elm in data:
                                if "title" in elm and "body" in elm:
                                    md += "# " + elm["title"] + "\n\n"
                                    md += elm["body"] + "\n\n"

                            #md_filepath = os.path.join(dir, filename + ".md")
                            md_filepath = re.sub(r"\.txt$", ".md", filepath)
                            with open(md_filepath, "w") as md_file:
                                md_file.write(md)

                            proccessed = True
                        except BaseException as e:
                            App.logger.debug('Error: {0}'.format(e.message))

                if os.path.isfile(filepath):
                    os.remove(filepath)

    return proccessed


def txt2usfm(rootdir="."):
    """
    Converts txt files to usfm
    """
    proccessed = False
    for dir, subdir, files in os.walk(rootdir):
        for fname in files:
            filepath = os.path.join(dir, fname)
            fileinfo = os.path.splitext(fname)

            filename = fileinfo[0]
            ext = fileinfo[1]

            if ext == ".txt":
                with open(filepath, "r") as data_file:
                    # if content of the file starts from the valid usfm chapter or verse tag
                    # then it's a usfm file
                    if re.match(r"^[\s]*\\c|^[\s]*\\v", data_file.read()):
                        os.rename(filepath, os.path.join(dir, filename + ".usfm"))

                        if os.path.isfile(filepath):
                            os.remove(filepath)

                        proccessed = True


    return proccessed
