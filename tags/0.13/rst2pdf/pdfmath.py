# -*- coding: utf-8 -*-
"""
    This is a dummy math extension.
    
    It's a hack, but if you want math in a PDF via pdfbuilder, and don't want to
    enable pngmath or jsmath, then enable this one.
    
    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx.errors import SphinxError
from sphinx.ext.mathbase import setup as mathbase_setup

class MathExtError(SphinxError):
    category = 'Math extension error'


def html_visit_math(self, node):
    self.body.append(node['latex'])
    raise nodes.SkipNode

def html_visit_displaymath(self, node):
    self.body.append(node['latex'])
    raise nodes.SkipNode


def setup(app):
    mathbase_setup(app, (html_visit_math, None), (html_visit_displaymath, None))
