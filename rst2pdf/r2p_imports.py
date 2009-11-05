# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

'''
We maintain imports of other packages in one place.  This gives us these
advantages:
    1) Slight efficiency gain
    2) Centralized exception handling for optional imports
'''

import sys
import os
import tempfile
import re
import string
import types
from os.path import abspath, dirname, expanduser, join
from urlparse import urljoin, urlparse, urlunparse
from copy import copy, deepcopy
from optparse import OptionParser
import logging

from docutils.languages import get_language
import docutils.readers.doctree
import docutils.core
import docutils.nodes
from docutils.parsers.rst import directives

import pygments_code_block_directive # code-block directive

from reportlab.platypus import *
from reportlab.platypus.flowables import _listWrapOn, _Container
from reportlab.pdfbase.pdfdoc import PDFPageLabel
from reportlab.lib.enums import *
from reportlab.lib.units import *
from reportlab.lib.pagesizes import *

from pprint import pprint

from roman import toRoman

# Is this really the best unescape in the stdlib for '&amp;' => '&'????
from xml.sax.saxutils import unescape, escape

from cStringIO import StringIO

try:
    from PIL import Image as PILImage
except ImportError:
    try:
        import Image as PILImage
    except ImportError:
        log.warning("Support for images other than JPG"
            " is now limited. Please install PIL.")
        PILImage = None

try:
    from PythonMagick import Image as PMImage
except ImportError:
    PMImage = None


try:
    import wordaxe
    from wordaxe.rl.paragraph import Paragraph
    from wordaxe.rl.styles import ParagraphStyle, getSampleStyleSheet
    # PyHnjHyphenator is broken for non-ascii characters, so
    # let's not use it and avoid useless crashes (http://is.gd/19efQ)

    #from wordaxe.PyHnjHyphenator import PyHnjHyphenator
    # If basehyphenator doesn't load, wordaxe is broken
    # pyhyphenator and DCW *may* not load.

    from wordaxe.BaseHyphenator import BaseHyphenator
    try:
        from wordaxe.plugins.PyHyphenHyphenator \
            import PyHyphenHyphenator
    except:
        pass
    try:
        from wordaxe.DCWHyphenator import DCWHyphenator
    except:
        pass

except ImportError:
    # log.warning("No support for hyphenation, install wordaxe")
    wordaxe = None

try:
    import sphinx
except ImportError:
    sphinx = None

try:
    import psyco
except ImportError:
    class psyco(object):
        @staticmethod
        def full():
            pass

#def escape (x,y):
#    "Dummy escape function to test for excessive escaping"
#    return x

