# -*- coding: utf-8 -*-
"""
    This is a dummy math extension.
    
    It's a hack, but if you want math in a PDF via pdfbuilder, and don't want to
    enable pngmath or jsmath, then enable this one.
    
    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import shutil
import tempfile
import posixpath
from os import path, getcwd, chdir
from subprocess import Popen, PIPE
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import sha

from docutils import nodes

from sphinx.errors import SphinxError
from sphinx.util import ensuredir
from sphinx.util.png import read_png_depth, write_png_depth
from sphinx.ext.mathbase import setup as mathbase_setup, wrap_displaymath

class MathExtError(SphinxError):
    category = 'Math extension error'


def html_visit_math(self, node):
    raise nodes.SkipNode

def html_visit_displaymath(self, node):
    raise nodes.SkipNode


def setup(app):
    mathbase_setup(app, (html_visit_math, None), (html_visit_displaymath, None))
