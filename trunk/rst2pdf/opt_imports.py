# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

'''
opt_imports.py contains logic for handling optional imports.

'''

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
    import psyco
except ImportError:
    class psyco(object):
        @staticmethod
        def full():
            pass

try:
    import aafigure
    import aafigure.pdfwordaxe_version
except ImportError:
    aafigure = None

try:
    from json import loads as json_loads
except ImportError:
    from simplejson import loads as json_loads

try:
    from reportlab.platypus.flowables import NullDraw
except ImportError: # Probably RL 2.1
    from reportlab.platypus.flowables import Flowable as NullDraw

try:
    from matplotlib import mathtext
except ImportError:
    mathtext = None
