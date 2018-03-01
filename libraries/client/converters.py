import os
import json
import re


def txt2md_json(rootdir="."):
    """
    Converts txt files with json data into markdown files
    """
    for dirs, subdirs, files in os.walk(rootdir):
        for fname in files:
            filepath = os.path.join(dirs, fname)
            fileinfo = os.path.splitext(fname)

            filename = fileinfo[0]
            ext = fileinfo[1]

            if ext == ".txt":
                with open(filepath, "r") as data_file:
                    data = json.load(data_file)
                    if data:
                        md = ""
                        for elm in data:
                            if "title" in elm and "body" in elm:
                                md += "# " + elm["title"] + "\n\n"
                                md += elm["body"] + "\n\n"

                        md_filepath = os.path.join(dirs, filename + ".md")

                        with open(md_filepath, "w") as md_file:
                            md_file.write(md)

                        if os.path.isfile(filepath):
                            os.remove(filepath)
