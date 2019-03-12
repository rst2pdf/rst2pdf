# -*- coding: utf-8 -*-

# See LICENSE.txt for licensing terms

'''
opt_imports.py contains logic for handling optional imports.

'''

import os
import sys

import six

from .log import log

PyHyphenHyphenator = None
DCWHyphenator = None
try:
    import wordaxe
    from wordaxe import version as wordaxe_version
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
    wordaxe_version = None
    BaseHyphenator = None
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus.paragraph import Paragraph


try:
    import sphinx
except ImportError:
    sphinx = None

try:
    import aafigure
    import aafigure.pdf
except ImportError:
    aafigure = None

try:
    from reportlab.platypus.flowables import NullDraw
except ImportError: # Probably RL 2.1
    from reportlab.platypus.flowables import Flowable as NullDraw

try:
    from matplotlib import mathtext
except ImportError:
    mathtext = None

import pdfrw as pdfinfo
from PIL import Image as PILImage
