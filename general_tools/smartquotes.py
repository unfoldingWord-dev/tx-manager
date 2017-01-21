#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#  Copyright (c) 2016 unfoldingWord
#  http://creativecommons.org/licenses/MIT/
#  See LICENSE file for details.
#
#  Contributors:
#  Jesse Griffin <jesse@distantshores.org>

"""
This script accepts a paragraph of input and outputs typographically correct
text using pandoc.  Note line breaks are not retained.
"""

from __future__ import unicode_literals
import shlex
from subprocess import *
import sys


def smartquotes(text):
    """
    Runs text through pandoc for smartquote correction.
    """
    command = shlex.split('pandoc --smart -t plain')
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = com.communicate(text.encode('utf-8'))
    com_out = out.decode('utf-8')
    text = com_out.replace(u'\n', u' ').strip()
    return text


if __name__ == '__main__':
    print(smartquotes(sys.stdin.read()))
