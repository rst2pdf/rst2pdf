# -*- coding: utf-8 -*-

#$URL$
#$Date$
#$Revision$

# See LICENSE.txt for licensing terms

'''
opt_imports.py contains logic for handling optional imports.

'''

import os
import sys

from log import log

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

class LazyImports(object):
    ''' Only import some things if we need them.
    '''

    def __getattr__(self, name):
        if name.startswith('_load_'):
            raise AttributeError
        value = None
        if not os.environ.get('DISABLE_' + name.upper()):
            func = getattr(self, '_load_' + name)
            try:
                value = func()
            except ImportError:
                pass
        # Cache the result once we have it
        setattr(self, name, value)
        return value

    def _load_pdfinfo(self):
        try:
            from pyPdf import pdf
        except ImportError:
            import pdfrw as pdf
        return pdf

    def _load_PILImage(self):
        try:
            from PIL import Image as PILImage
        except ImportError:
            import Image as PILImage
        return PILImage

    def _load_PMImage(self):
        from PythonMagick import Image
        return Image

    def _load_gfx(self):
        import gfx
        return gfx

    def _load_svglib(self):
        from svglib import svglib
        return svglib

    def _load_uniconvertor(self):
        for p in sys.path:
            d = os.path.join(p, 'uniconvertor')
            if os.path.isdir(d):
                sys.path.append(d)
                from app.io import load
                from app.plugins import plugins
                import app
                from uniconvsaver import save
                app.init_lib()
                plugins.load_plugin_configuration()
                break
        else:
            raise ImportError
        return load, plugins, save

LazyImports = LazyImports()
