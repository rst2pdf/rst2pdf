# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

'''
We maintain imports of other packages in one place.  This gives us these
advantages:
    1) Slight efficiency gain
    2) Notifications of symbol interference
    3) Better control of optional imports
    4) Just type 'r2p_imports.py xxx' to figure out where the heck xxx came from!!!
'''

unconditionalimports = '''
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
'''

def loadunconditional():
    def setpaths():
        import os
        thisdir = os.path.dirname(__file__)
        scriptfile = os.path.join(thisdir, '..', 'bin', 'rst2pdf')
        f = open(scriptfile, 'rb')
        data = f.read()
        f.close()
        data = data.split('import rst2pdf')[0]
        exec data in {}
    if __name__ == '__main__':
        setpaths()
    importinfo = {}
    badimports = []
    globaldir = {}
    for i, line in enumerate(unconditionalimports.splitlines()):
        line = line.split('#')[0].rstrip()
        if not line:
            continue
        newdir = {}
        try:
            exec line in newdir
        except:
            print line
            raise
        line = '%s # %d' % (line, i)
        for key, value in newdir.iteritems():
            oldline = importinfo.setdefault(key, line)
            if oldline is not line and value is not globaldir[key]:
                badimports.append((key, oldline, line))
        globaldir.update(newdir)

    if badimports:
        badimports = ['%s defined by "%s" and "%s' % x for x in badimports]
        badimports = '\n        '.join(badimports)
        raise SystemExit('\nError: conflicting imported symbols:\n\n%s\n' %
                            badimports)

    return globaldir, importinfo

_unconditional, _unconditional_info = loadunconditional()

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

def dumpinfo(varnames):
    import inspect
    print
    g = globals()
    for name in varnames:
        if name not in g:
            print '%s not defined globally' % repr(name)
            continue
        value = g[name]
        info = '%s (value %s)' % (repr(name), repr(value))
        line = _unconditional_info.get(name)
        if line is not None:
            print '%s imported with %s' % (
                    info, repr(line.split('#')[0].rstrip()))
        else:
            print '%s imported or defined explicitly (see source code)'
        try:
            sourcef = inspect.getfile(value)
        except TypeError:
            pass
        else:
            if sourcef.endswith('.pyc'):
                sourcef = sourcef[:-1]
            print '      defined in %s' % sourcef
    print

def checkconditional():
    ignore = set('__builtins__ Paragraph ParagraphStyle getSampleStyleSheet'.split())
    globaldict = globals()
    unconditional = _unconditional
    globalset = set(globaldict)
    unconditionalset = set(unconditional)
    common = (globalset & unconditionalset) - ignore
    common = sorted(x for x in common if globaldict[x] is not unconditional[x])
    if common:
        raise SystemExit('imports redefined conditionally: %s' % ', '.join(common))
    globaldict.update(unconditional)
checkconditional()

#def escape (x,y):
#    "Dummy escape function to test for excessive escaping"
#    return x

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print "\nAll imports are fine.  Type r2p_imports.py <name> to see where a name comes from.\n"
    else:
        dumpinfo(sys.argv[1:])

del unconditionalimports, loadunconditional, _unconditional, _unconditional_info
del dumpinfo, checkconditional
