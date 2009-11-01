# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

# Some fragments of code are copied from Reportlab under this license:
#
#####################################################################################
#
#       Copyright (c) 2000-2008, ReportLab Inc.
#       All rights reserved.
#
#       Redistribution and use in source and binary forms, with or without modification,
#       are permitted provided that the following conditions are met:
#
#               *       Redistributions of source code must retain the above copyright notice,
#                       this list of conditions and the following disclaimer.
#               *       Redistributions in binary form must reproduce the above copyright notice,
#                       this list of conditions and the following disclaimer in the documentation
#                       and/or other materials provided with the distribution.
#               *       Neither the name of the company nor the names of its contributors may be
#                       used to endorse or promote products derived from this software without
#                       specific prior written permission.
#
#       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#       ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#       WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#       IN NO EVENT SHALL THE OFFICERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#       INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
#       TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#       OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
#       IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#       IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#       SUCH DAMAGE.
#
#####################################################################################


__docformat__ = 'reStructuredText'

# Import Psyco if available
try:
    import psyco
    psyco.full()
except ImportError:
    pass

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
#from reportlab.lib.enums import *
#from reportlab.lib.units import *
#from reportlab.lib.pagesizes import *

from flowables import * # our own reportlab flowables
import flowables

from svgimage import SVGImage
from math_directive import math_node
from math_flowable import Math
from aafigure_directive import Aanode

from log import log, nodeid
from pprint import pprint

from smartypants import smartyPants

from roman import toRoman

# Is this really the best unescape in the stdlib for '&amp;' => '&'????
from xml.sax.saxutils import unescape, escape

import config

from cStringIO import StringIO

#def escape (x,y):
#    "Dummy escape function to test for excessive escaping"
#    return x
from utils import log, parseRaw
import styles as sty

HAS_PIL = True
try:
    from PIL import Image as PILImage
except ImportError:
    try:
        import Image as PILImage
    except ImportError:
        log.warning("Support for images other than JPG,"
            " is now limited. Please install PIL.")
        HAS_PIL = False

try:
    from PythonMagick import Image as PMImage
    HAS_MAGICK = True
except ImportError:
    HAS_MAGICK = False


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
    HAS_WORDAXE = False
else:
    HAS_WORDAXE = True

try:
    import sphinx
    HAS_SPHINX = True
except ImportError:
    HAS_SPHINX = False

import genpdftext
import genelements

class RstToPdf(object):

    def __init__(self, stylesheets=[], language=None,
                 header=None,
                 footer=None,
                 inlinelinks=False,
                 breaklevel=1,
                 font_path=[],
                 style_path=[],
                 fit_mode='shrink',
                 sphinx=False,
                 smarty='0',
                 baseurl=None,
                 repeat_table_rows=False,
                 footnote_backlinks=True,
                 inline_footnotes=False,
                 def_dpi=300,
                 show_frame=False,
                 highlightlang='python', #This one is only used by sphinx
                 basedir=os.getcwd(),
                 splittables=False,
                 blank_first_page=False,
                 breakside='odd'
                 ):
        global HAS_SPHINX
        self.debugLinesPdf=False
        self.depth=0
        self.breakside=breakside
        self.blank_first_page=blank_first_page
        self.splittables=splittables
        self.basedir=basedir
        self.language = language
        self.doc_title = ""
        self.doc_author = ""
        self.header = header
        self.footer = footer
        self.decoration = {'header': header,
                           'footer': footer,
                           'endnotes': []}
        # find base path
        if hasattr(sys, 'frozen'):
            self.PATH = abspath(dirname(sys.executable))
        else:
            self.PATH = abspath(dirname(__file__))
            
            
        self.font_path=font_path
        self.style_path=style_path
        self.def_dpi=def_dpi
        self.loadStyles(stylesheets)
            
        self.docutils_languages = {}
        self.inlinelinks = inlinelinks
        self.breaklevel = breaklevel
        self.fit_mode = fit_mode
        self.to_unlink = []
        self.smarty = smarty
        self.baseurl = baseurl
        self.repeat_table_rows = repeat_table_rows
        self.footnote_backlinks = footnote_backlinks
        self.inline_footnotes = inline_footnotes
        self.def_dpi = def_dpi
        self.show_frame = show_frame
        self.img_dir = os.path.join(abspath(dirname(__file__)), 'images')

        # Sorry about this, but importing sphinx.roles makes some
        # ordinary documents fail (demo.txt specifically) so
        # I can' t just try to import it outside. I need
        # to do it only if it's requested
        if HAS_SPHINX and sphinx:
            import sphinx.roles
            self.highlightlang = highlightlang
            genpdftext.add_sphinx()
            genelements.add_sphinx()
        else:
            HAS_SPHINX = False
            directives.register_directive('code-block', pygments_code_block_directive.code_block_directive)

        if not self.styles.languages:
            self.styles.languages=[]
            if self.language:
                self.styles.languages.append(self.language)
                self.styles['bodytext'].language = self.language

        # Load the docutils language modules for all required languages
        for lang in self.styles.languages:
            try:
                self.docutils_languages[lang] = get_language(lang)
            except ImportError:
                try:
                    self.docutils_languages[lang] = \
                         get_language(lang.split('_', 1)[0])
                except ImportError:
                    log.warning("Can't load Docutils module \
                        for language %s", lang)

        # Load the hyphenators for all required languages
        if HAS_WORDAXE:
            for lang in self.styles.languages:
                if lang.split('_', 1)[0] == 'de':
                    try:
                        wordaxe.hyphRegistry[lang] = DCWHyphenator('de', 5)
                        continue
                    except Exception:
                        # hyphenators may not always be available or crash,
                        # e.g. wordaxe issue 2809074 (http://is.gd/16lqs)
                        log.warning("Can't load wordaxe DCW hyphenator "
                        "for German language, trying Py hyphenator instead")
                    else:
                        continue
                try:
                    wordaxe.hyphRegistry[lang] = PyHyphenHyphenator(lang)
                except Exception:
                    log.warning("Can't load wordaxe Py hyphenator"
                        " for language %s, trying base hyphenator", lang)
                else:
                    continue
                try:
                    wordaxe.hyphRegistry[lang] = BaseHyphenator(lang)
                except Exception:
                    log.warning("Can't even load wordaxe base hyphenator")
            log.info('hyphenation by default in %s , loaded %s',
                self.styles['bodytext'].language,
                ','.join(self.styles.languages))

        self.pending_targets=[]
        self.targets=[]
        
    def loadStyles(self, styleSheets=None ):
        
        if styleSheets is None:
            styleSheets=[]
        
        self.styles = sty.StyleSheet(styleSheets,
                                     self.font_path,
                                     self.style_path,
                                     def_dpi=self.def_dpi)


    def size_for_image_node(self, node):
        imgname = os.path.join(self.basedir,str(node.get("uri")))
        scale = float(node.get('scale', 100))/100

        # Figuring out the size to display of an image is ... annoying.
        # If the user provides a size with a unit, it's simple, adjustUnits
        # will return it in points and we're done.

        # However, often the unit wil be "%" (specially if it's meant for
        # HTML originally. In which case, we will use a percentage of
        # the containing frame.

        # Find the image size in pixels:
        kind = 'direct'
        xdpi, ydpi = self.styles.def_dpi, self.styles.def_dpi
        extension = imgname.split('.')[-1].lower()
        if extension in [
                "ai", "ccx", "cdr", "cgm", "cmx",
                "sk1", "sk", "svg", "xml", "wmf", "fig"]:
            iw, ih = SVGImage(imgname).wrap(0, 0)
            # These are in pt, so convert to px
            iw = iw * xdpi / 72
            ih = ih * ydpi / 72
        elif extension == 'pdf':
            try:
                from pyPdf import pdf
            except:
                log.warning('PDF images are not supported without pypdf [%s]', nodeid(node))
                return 0, 0, 'direct'
            reader = pdf.PdfFileReader(open(imgname))
            x1, y1, x2, y2 = reader.getPage(0)['/MediaBox']
            # These are in pt, so convert to px
            iw = float((x2-x1) * xdpi / 72)
            ih = float((y2-y1) * ydpi / 72)
        else:
            if HAS_PIL:
                img = PILImage.open(imgname)
                iw, ih = img.size
                xdpi, ydpi = img.info.get('dpi', (xdpi, ydpi))
            elif HAS_MAGICK:
                img = PMImage(imgname)
                iw = img.size().width()
                ih = img.size().height()
                # FIXME: need to figure out how to get the DPI
                # xdpi, ydpi=img.density().???
            else:
                log.warning("Sizing images without PIL "
                            "or PythonMagick, using 100x100 [%s]"
                            , nodeid(node))
                iw, ih = 100., 100.

        # Try to get the print resolution from the image itself via PIL.
        # If it fails, assume a DPI of 300, which is pretty much made up,
        # and then a 100% size would be iw*inch/300, so we pass
        # that as the second parameter to adjustUnits
        #
        # Some say the default DPI should be 72. That would mean
        # the largest printable image in A4 paper would be something
        # like 480x640. That would be awful.
        #

        w = node.get('width')
        if w is not None:
            # In this particular case, we want the default unit
            # to be pixels so we work like rst2html
            if w[-1] == '%':
                kind = 'percentage_of_container'
                w=int(w[:-1])
            else:
                # This uses default DPI setting because we
                # are not using the image's "natural size"
                # this is what LaTeX does, according to the
                # docutils mailing list discussion
                w = self.styles.adjustUnits(w, self.styles.tw,
                                            default_unit='px')
        else:
            log.warning("Using image %s without specifying size."
                "Calculating based on image size at %ddpi [%s]",
                imgname, xdpi, nodeid(node))
            # No width specified at all, use w in px
            w = iw*inch/xdpi

        h = node.get('height')
        if h is not None and h[-1] != '%':
            h = self.styles.adjustUnits(h, ih*inch/ydpi)
        else:
            # Now, often, only the width is specified!
            # if we don't have a height, we need to keep the
            # aspect ratio, or else it will look ugly
            if h and h[-1]=='%':
                log.error('Setting height as a percentage does **not** work. '\
                          'ignoring height parameter [%s]', nodeid(node))
            h = w*ih/iw

        # Apply scale factor
        w = w*scale
        h = h*scale

        # And now we have this probably completely bogus size!
        log.info("Image %s size calculated:  %fcm by %fcm [%s]",
            imgname, w/cm, h/cm, nodeid(node))

        return w, h, kind

    def style_language(self, style):
        """Return language corresponding to this style."""
        try:
            return style.language
        except AttributeError:
            pass
        try:
            return self.styles['bodytext'].language
        except AttributeError:
            # FIXME: this is pretty arbitrary, and will
            # probably not do what you want.
            # however, it should only happen if:
            # * You specified the language of a style
            # * Have no wordaxe installed.
            # Since it only affects hyphenation, and wordaxe is
            # not installed, t should have no effect whatsoever
            return os.environ['LANG'] or 'en'

    def text_for_label(self, label, style):
        """Translate text for label."""
        try:
            text = self.docutils_languages[self.style_language(style)]\
                    .labels[label]
        except KeyError:
            text = label.capitalize()
        return text + ":"

    def text_for_bib_field(self, field, style):
        """Translate text for bibliographic fields."""
        try:
            text = self.docutils_languages[self.style_language(style)]\
                    .bibliographic_fields[field]
        except KeyError:
            text = field
        return text + ":"

    def author_separator(self, style):
        """Return separator string for authors."""
        try:
            sep = self.docutils_languages[self.style_language(style)]\
                    .author_separators[0]
        except KeyError:
            sep = ';'
        return sep + " "

    def styleToFont(self, style):
        '''Takes a style name, returns a font tag for it, like
        "<font face=helvetica size=14 color=red>". Used for inline
        nodes (custom interpreted roles)'''

        try:
            s = self.styles[style]
            bc = s.backColor
            if bc:
                r = '<font face="%s" size="%d" color="#%s" backColor="#%s">'\
                    %(s.fontName, s.fontSize,
                      s.textColor.hexval()[2:], bc.hexval()[2:])
            else:
                r = '<font face="%s" size="%d" color="#%s">' % (
                    s.fontName, s.fontSize, s.textColor.hexval()[2:])
            return r
        except KeyError:
            log.warning('Unknown class %s', style)
            return None

    def gather_pdftext(self, node, replaceEnt=True):
        return ''.join([self.gen_pdftext(n, replaceEnt)
            for n in node.children])

    def gen_pdftext(self, node, replaceEnt=True):
        return genpdftext.dispatch(self, node, replaceEnt)

    def gen_elements(self, node, style=None):
        return genelements.dispatch(self, node, style)

    def gather_elements(self, node, style=None):
        if style is None:
            style = self.styles.styleForNode(node)
        r = []
        if 'float' in style.__dict__:
            style = None # Don't pass floating styles to children!
        for n in node.children:
            # import pdb; pdb.set_trace()
            r.extend(self.gen_elements(n, style=style))
        return r

    def bullet_for_node(self, node):
        """Takes a node, assumes it's some sort of
           item whose parent is a list, and
           returns the bullet text it should have"""
        b = ""
        t = 'item'
        if node.parent.get('start'):
            start = int(node.parent.get('start'))
        else:
            start = 1

        if node.parent.get('bullet') or \
            isinstance(node.parent, docutils.nodes.bullet_list):
            b = node.parent.get('bullet','*')
            if b == "None":
                b = ""
            t = 'bullet'

        elif node.parent.get('enumtype')=='arabic':
            b = str(node.parent.children.index(node) + start) + '.'

        elif node.parent.get('enumtype') == 'lowerroman':
            b = toRoman(node.parent.children.index(node) + start).lower() + '.'
        elif node.parent.get('enumtype') == 'upperroman':
            b = toRoman(node.parent.children.index(node) + start).upper() + '.'
        elif node.parent.get('enumtype') == 'loweralpha':
            b = string.lowercase[node.parent.children.index(node)
                + start - 1] + '.'
        elif node.parent.get('enumtype') == 'upperalpha':
            b = string.uppercase[node.parent.children.index(node)
                + start - 1] + '.'
        else:
            log.critical("Unknown kind of list_item %s [%s]",
                node.parent, nodeid(node))
        return b, t

    def filltable(self, rows):
        """
        Takes a list of rows, consisting of cells and performs the following fixes:

        * For multicolumn cells, add continuation cells, to make all rows the same
        size.

        * For multirow cell, insert continuation cells, to make all columns the
        same size.

        * If there are still shorter rows, add empty cells at the end (ReST quirk)

        * Once the table is *normalized*, create spans list, fitting for reportlab's
        Table class.

        """

        # If there is a multicol cell, we need to insert Continuation Cells
        # to make all rows the same length

        for y in range(0, len(rows)):
            for x in range(0, len(rows[y])):
                cell = rows[y][x]
                if isinstance(cell, str):
                    continue
                if cell.get("morecols"):
                    for i in range(0, cell.get("morecols")):
                        rows[y].insert(x + 1, "")

        for y in range(0, len(rows)):
            for x in range(0, len(rows[y])):
                cell = rows[y][x]
                if isinstance(cell, str):
                    continue
                if cell.get("morerows"):
                    for i in range(0, cell.get("morerows")):
                        rows[y + i + 1].insert(x, "")


        # If a row is shorter, add empty cells at the right end
        maxw = max([len(r) for r in rows])
        for r in rows:
            while len(r) < maxw:
                r.append("")

        # Create spans list for reportlab's table style
        spans = []
        for y in range(0, len(rows)):
            for x in range(0, len(rows[y])):
                cell = rows[y][x]
                if isinstance(cell, str):
                    continue
                if cell.get("morecols"):
                    mc = cell.get("morecols")
                else:
                    mc = 0
                if cell.get("morerows"):
                    mr = cell.get("morerows")
                else:
                    mr = 0
                if mc or mr:
                    spans.append(('SPAN', (x, y), (x + mc, y + mr)))
        return spans

    def PreformattedFit(self, text, style):
        """Preformatted section that gets horizontally compressed if needed."""
        # Pass a ridiculous size, then it will shrink to what's available
        # in the frame
        return BoundByWidth(2000*cm,
            content=[XPreformatted(text, style)],
            mode=self.fit_mode, style=style)

    def createPdf(self, text=None, 
                  source_path=None, 
                  output=None, 
                  doctree=None,
                  compressed=False,
                  # This adds entries to the PDF TOC
                  # matching the rst source lines
                  debugLinesPdf=False):
        """Create a PDF from text (ReST input),
        or doctree (docutil nodes) and save it in outfile.

        If outfile is a string, it's a filename.
        If it's something with a write method, (like a StringIO,
        or a file object), the data is saved there.

        """
        self.decoration = {'header': self.header,
                           'footer': self.footer,
                           'endnotes': []}
                           
        self.pending_targets=[]
        self.targets=[]

        self.debugLinesPdf = debugLinesPdf

        if doctree is None:
            if text is not None:
                if self.language:
                    settings_overrides={'language_code': self.language[:2]}
                else:
                    settings_overrides={}
                self.doctree = docutils.core.publish_doctree(text,
                    source_path=source_path,
                    settings_overrides=settings_overrides)
                log.debug(self.doctree)
            else:
                log.error('Error: createPdf needs a text or a doctree')
                return
        else:
            self.doctree = doctree

        elements = self.gen_elements(self.doctree)

        if self.blank_first_page:
            elements.insert(0,PageBreak())

        # Put the endnotes at the end ;-)
        endnotes = self.decoration['endnotes']
        if endnotes:
            elements.append(Spacer(1, 2*cm))
            elements.append(Separation())
            for n in self.decoration['endnotes']:
                t_style = TableStyle(self.styles['endnote'].commands)
                colWidths = self.styles['endnote'].colWidths
                elements.append(DelayedTable([[n[0], n[1]]],
                    style=t_style, colWidths=colWidths))

        head = self.decoration['header']
        foot = self.decoration['footer']

        # So, now, create the FancyPage with the right sizes and elements
        FP = FancyPage("fancypage", head, foot, self.styles,
                       smarty=self.smarty, show_frame=self.show_frame)

        pdfdoc = FancyDocTemplate(
            output,
            pageTemplates=[FP],
            showBoundary=0,
            pagesize=self.styles.ps,
            title=self.doc_title,
            author=self.doc_author,
            pageCompression=compressed)
        while True:
            try:
                log.info("Starting build")
                pdfdoc.multiBuild(elements)
                break
            except ValueError, v:
                # FIXME: cross-document links come through here, which means
                # an extra pass per cross-document reference. Which sucks.
                if v.args and str(v.args[0]).startswith('format not resolved'):
                    missing=str(v.args[0]).split(' ')[-1]
                    log.error('Adding missing reference to %s and rebuilding. This is slow!'%missing)
                    elements.append(Reference(missing))
                    for e in elements:
                        if hasattr(e,'_postponed'):
                            delattr(e,'_postponed')
                else:
                    raise
        #doc = SimpleDocTemplate("phello.pdf")
        #doc.build(elements)
        for fn in self.to_unlink:
            os.unlink(fn)


class FancyDocTemplate(BaseDocTemplate):

    #def multiBuild(self, story,
                   #filename=None,
                   #canvasmaker=canvas.Canvas,
                   #maxPasses = 10):
        #"""Makes multiple passes until all indexing flowables
        #are happy."""

        #self._indexingFlowables = []
        ##scan the story and keep a copy
        #for thing in story:
            #if thing.isIndexing():
                #self._indexingFlowables.append(thing)

        ##better fix for filename is a 'file' problem
        #self._doSave = 0
        #passes = 0
        #mbe = []
        #self._multiBuildEdits = mbe.append
        #while 1:
            #s=story[-202].style
            #for n in dir(s):
                #if not n.startswith('_'):
                    #print n,eval('s.parent.%s'%n)
            #print '----------------------'
            #passes += 1
            #log.info('Pass number %d'%passes)

            #for fl in self._indexingFlowables:
                #fl.beforeBuild()

            ## work with a copy of the story, since it is consumed
            #tempStory = story[:]
            #self.build(tempStory, filename, canvasmaker)
            ##self.notify('debug',None)

            #for fl in self._indexingFlowables:
                #fl.afterBuild()

            #happy = self._allSatisfied()

            #if happy:
                #self._doSave = 0
                #self.canv.save()
                #break
            #else:
                #self.canv.save()
                #f=open('pass-%d.pdf'%passes,'wb')
                #f.seek(0)
                #f.truncate()
                #f.write(self.filename.getvalue())
                #self.filename = StringIO()
            #if passes > maxPasses:
                ## Don't fail, just say that the indexes may be wrong
                #log.error("Index entries not resolved after %d passes" % maxPasses)
                #break


            ##work through any edits
            #while mbe:
                #e = mbe.pop(0)
                #e[0](*e[1:])

        #del self._multiBuildEdits
        #if verbose: print 'saved'


    def afterFlowable(self, flowable):

        if isinstance(flowable, Heading):
            # Notify TOC entry for headings/abstracts/dedications.
            level, text = flowable.level, flowable.text
            parent_id = flowable.parent_id
            node = flowable.node  
            pagenum = setPageCounter()
            self.notify('TOCEntry', (level, text, pagenum, parent_id, node))

_counter=0
_counterStyle='arabic'

class PageCounter(Flowable):

    def __init__(self, number=0, style='arabic'):
        self.style=str(style).lower()
        self.number=int(number)
        Flowable.__init__(self)

    def drawOn(self, canvas, x, y, _sW):
        global _counter, _counterStyle
        _counterStyle=self.style
        _counter=self.number

flowables.PageCounter = PageCounter

def setPageCounter(counter=None, style=None):

    global _counter, _counterStyle

    if counter is not None:
        _counter = counter
    if style is not None:
        _counterStyle = style

    if _counterStyle=='lowerroman':
        ptext=toRoman(_counter).lower()
    elif _counterStyle=='roman':
        ptext=toRoman(_counter).upper()
    elif _counterStyle=='alpha':
        ptext=string.uppercase[_counter%26]
    elif _counterStyle=='loweralpha':
        ptext=string.lowercase[_counter%26]
    else:
        ptext=unicode(_counter)
    return ptext


class HeaderOrFooter(object):
    """ A helper object for FancyPage (below)
        HeaderOrFooter exists for two reasons:
            1) to handle operations which are common to both headers
               and footers; and
            2) to thwart deepcopy when it attempts to copy things
               which it shouldn't (see issue # 126)
    """
    def __init__(self, items=None, isfooter=False):
        self.items = items
        if isfooter:
            locinfo = 'footer showFooter defaultFooter'
        else:
            locinfo = 'header showHeader defaultHeader'
        self.isfooter = isfooter
        self.loc, self.showloc, self.defaultloc = locinfo.split()

    def __deepcopy__(self, *whatever):
        return HeaderOrFooter(copy(self.items), self.isfooter)

    def prepare(self, pageobj, canv):
        showloc = pageobj.template.get(self.showloc, True)
        items = self.items
        if showloc and not items:
            items = pageobj.template.get(self.defaultloc)
        if items:
            if isinstance(items, list):
                items = items[:]
            else:
                items = [Paragraph(items, pageobj.styles[self.loc])]
            _, height =  _listWrapOn(items, pageobj.tw, canv)
        else:
            height = 0
        self.prepared = items
        return height

    def replaceTokens(self, elems, canv, doc, smarty):
        """Put doc_title/page number/etc in text of header/footer."""

        # Make sure page counter is up to date
        pnum=setPageCounter()

        for e in elems:
            i = elems.index(e)
            if isinstance(e, Paragraph):
                text = e.text
                if not isinstance(text, unicode):
                    try:
                        text = unicode(text, e.encoding)
                    except AttributeError:
                        text = unicode(text, 'utf-8')

                text = text.replace(u'###Page###', pnum)
                text = text.replace(u"###Title###", doc.title)
                text = text.replace(u"###Section###",
                    getattr(canv, 'sectName', ''))
                text = text.replace(u"###SectNum###",
                    getattr(canv, 'sectNum', ''))
                text = smartyPants(text, smarty)
                elems[i] = Paragraph(text, e.style)

    def draw(self, pageobj, canv, doc, x, y, width, height):
        items = self.prepared
        if items:
            self.replaceTokens(items, canv, doc, pageobj.smarty)
            container = _Container()
            container._content = items
            container.width = width
            container.height = height
            container.drawOn(canv, x, y)


class FancyPage(PageTemplate):
    """ A page template that handles changing layouts.
    """

    def __init__(self, _id, _head, _foot, styles, smarty="0", show_frame=False):
        self.styles = styles
        self._head = HeaderOrFooter(_head)
        self._foot = HeaderOrFooter(_foot, True)
        self.smarty = smarty
        self.show_frame = show_frame
        PageTemplate.__init__(self, _id, [])


    def beforeDrawPage(self, canv, doc):
        """Do adjustments to the page according to where we are in the document.

           * Gutter margins on left or right as needed

        """

        #from pudb import set_trace; set_trace()
        global _counter, _counterStyle

        self.tw = self.styles.pw - self.styles.lm -\
            self.styles.rm - self.styles.gm
        # What page template to use?
        tname = canv.__dict__.get('templateName',
                                  self.styles.firstTemplate)
        self.template = self.styles.pageTemplates[tname]
        canv.templateName=tname

        doct = getattr(canv, '_doctemplate', None)
        canv._doctemplate = None # to make _listWrapOn work

        if doc.page==1:
            _counter=0
            _counterStyle='arabic'
        _counter+=1

        # Adjust text space accounting for header/footer
        
        self.hh = self._head.prepare(self, canv)
        self.fh = self._foot.prepare(self, canv)
            
        canv._doctemplate = doct

        self.hx = self.styles.lm
        self.hy = self.styles.ph - self.styles.tm -self.hh

        self.fx = self.styles.lm
        self.fy = self.styles.bm
        self.th = self.styles.ph - self.styles.tm - \
            self.styles.bm - self.hh - self.fh - \
            self.styles.ts - self.styles.bs
            
        # Adjust gutter margins
        if doc.page % 2: # Left page
            x1 = self.styles.lm
        else: # Right page
            x1 = self.styles.lm + self.styles.gm
        y1 = self.styles.bm + self.fh + self.styles.bs
        
        # If there is a background parameter for this page Template, draw it
        if 'background' in self.template:
            uri=self.template['background']
            if os.path.exists(uri):
                if uri.split('.')[-1].lower() in [
                        "ai", "ccx", "cdr", "cgm", "cmx",
                        "sk1", "sk", "svg", "xml", "wmf", "fig"]:
                    bg = SVGImage(uri, self.styles.pw, self.styles.ph)
                else:
                    bg = Image(uri, self.styles.pw, self.styles.ph)
                bg.drawOn(canv, 0, 0)
            else:
                log.error("Missing background image file: %s", uri)

        self.frames = []
        for frame in self.template['frames']:
            self.frames.append(SmartFrame(self,
                self.styles.adjustUnits(frame[0], self.tw) + x1,
                self.styles.adjustUnits(frame[1], self.th) + y1,
                self.styles.adjustUnits(frame[2], self.tw),
                self.styles.adjustUnits(frame[3], self.th),
                    showBoundary=self.show_frame))
        canv.firstSect=True
        canv._pagenum=doc.page
        for frame in self.frames:
            frame._pagenum=doc.page

    def afterDrawPage(self, canv, doc):
        """Draw header/footer."""
        # Adjust for gutter margin
        log.info('Page %s [%s]'%(_counter,doc.page))
        if doc.page % 2: # Left page
            hx = self.hx
            fx = self.fx
        else: # Right Page
            hx = self.hx + self.styles.gm
            fx = self.fx + self.styles.gm
            
        self._head.draw(self, canv, doc, hx, self.hy, self.tw, self.hh)
        self._foot.draw(self, canv, doc, fx, self.fy, self.tw, self.fh)

def parse_commandline():
    
    parser = OptionParser()
    
    parser.add_option('--config', dest='configfile', metavar='FILE',
        help='Config file to use. Default=~/.rst2pdf/config')
    
    parser.add_option('-o', '--output', dest='output', metavar='FILE',
        help='Write the PDF to FILE')

    def_ssheets = ','.join([expanduser(p) for p in
        config.getValue("general", "stylesheets", "").split(',')])
    parser.add_option('-s', '--stylesheets', dest='style',
        type='string', action='append',
        metavar='STYLESHEETS', default=[def_ssheets],
        help='A comma-separated list of custom stylesheets.'\
        ' Default="%s"' % def_ssheets)

    def_sheetpath = os.pathsep.join([expanduser(p) for p in
        config.getValue("general", "stylesheet_path", "").split(os.pathsep)])
    parser.add_option('--stylesheet-path', dest='stylepath',
        metavar='FOLDER%sFOLDER%s...%sFOLDER'%((os.pathsep, )*3),
        default=def_sheetpath,
        help='A list of folders to search for stylesheets,"\
        " separated using "%s". Default="%s"' %(os.pathsep, def_sheetpath))

    def_compressed = config.getValue("general", "compressed", False)
    parser.add_option('-c', '--compressed', dest='compressed',
        action="store_true", default=def_compressed,
        help='Create a compressed PDF. Default=%s'%def_compressed)

    parser.add_option('--print-stylesheet', dest='printssheet',
        action="store_true", default=False,
        help='Print the default stylesheet and exit')

    parser.add_option('--font-folder', dest='ffolder', metavar='FOLDER',
        help='Search this folder for fonts. (Deprecated)')

    def_fontpath = os.pathsep.join([expanduser(p) for p in
        config.getValue("general", "font_path", "").split(os.pathsep)])
    parser.add_option('--font-path', dest='fpath',
        metavar='FOLDER%sFOLDER%s...%sFOLDER'%((os.pathsep, )*3),
        default=def_fontpath,
        help='A list of folders to search for fonts,'\
             ' separated using "%s". Default="%s"'%(os.pathsep, def_fontpath))

    def_baseurl = urlunparse(['file',os.getcwd(),'','','',''])
    parser.add_option('--baseurl', dest='baseurl', metavar='URL',
        default=def_baseurl,
        help='The base URL for relative URLs. Default="%s"'%def_baseurl)

    def_lang = config.getValue("general", "language", None)
    parser.add_option('-l', '--language', metavar='LANG',
        default=def_lang, dest='language',
        help='Language to be used for hyphenation and '\
        'docutils localizations. Default="%s"' % def_lang)

    def_header = config.getValue("general", "header")
    parser.add_option('--header', metavar='HEADER',
        default=def_header, dest='header',
        help='Page header if not specified in the document.'\
        ' Default="%s"' % def_header)

    def_footer = config.getValue("general", "footer")
    parser.add_option('--footer', metavar='FOOTER',
        default=def_footer, dest='footer',
        help='Page footer if not specified in the document.'\
        ' Default="%s"' % def_footer)

    def_smartquotes = config.getValue("general", "smartquotes", "0")
    parser.add_option("--smart-quotes", metavar="VALUE",
        default=def_smartquotes, dest="smarty",
        help='Try to convert ASCII quotes, ellipsis and dashes '\
        'to the typographically correct equivalent. For details,'\
        ' read the man page or the manual. Default="%s"'%def_smartquotes)

    def_fit = config.getValue("general", "fit_mode", "shrink")
    parser.add_option('--fit-literal-mode', metavar='MODE',
        default=def_fit, dest='fit_mode',
        help='What todo when a literal is too wide. One of error,'\
        ' overflow,shrink,truncate. Default="%s"'%def_fit)

    parser.add_option('--inline-links', action="store_true",
    dest='inlinelinks', default=False,
        help='shows target between parenthesis instead of active link')

    parser.add_option('--repeat-table-rows', action="store_true",
        dest='repeattablerows', default=False,
        help='Repeats header row for each splitted table')

    parser.add_option('-q', '--quiet', action="store_true",
        dest='quiet', default=False,
        help='Print less information.')

    parser.add_option('-v', '--verbose', action="store_true",
        dest='verbose', default=False,
        help='Print debug information.')

    parser.add_option('--very-verbose', action="store_true",
        dest='vverbose', default=False,
        help='Print even more debug information.')

    parser.add_option('--version', action="store_true",
        dest='version', default=False,
        help='Print version number and exit.')

    def_footnote_backlinks = config.getValue("general",
        "footnote_backlinks", True)
    parser.add_option('--no-footnote-backlinks', action='store_false',
        dest='footnote_backlinks', default=def_footnote_backlinks,
        help='Disable footnote backlinks.'\
        ' Default=%s' % str(not def_footnote_backlinks))

    def_inline_footnotes = config.getValue("general",
        "inline_footnotes", False)
    parser.add_option('--inline-footnotes', action='store_true',
        dest='inline_footnotes', default=def_inline_footnotes,
        help='Show footnotes inline.'\
        ' Default=%s' % str(not def_inline_footnotes))

    def_dpi = config.getValue("general", "default_dpi", 300)
    parser.add_option('--default-dpi', dest='def_dpi', metavar='NUMBER',
        default=def_dpi,
        help='DPI for objects sized in pixels. Default=%d'%def_dpi)

    parser.add_option('--show-frame-boundary', dest='show_frame',
        action='store_true', default=False,
        help='Show frame borders (only useful for debugging). Default=False')

    parser.add_option('--disable-splittables', dest='splittables',
        action='store_false', default=True,
        help='Don\'t use splittable flowables in some elements. '
        'Only try this if you can\'t process a document any other way.')

    def_break = config.getValue("general", "break_level", 0)
    parser.add_option('-b', '--break-level', dest='breaklevel',
        metavar='LEVEL', default=def_break,
        help='Maximum section level that starts in a new page.'\
        ' Default: %d' % def_break)

    def_fpeven = config.getValue("general", "first_page_even", False)
    parser.add_option('--first-page-even', dest='first_page_even',
        action='store_true', default=def_fpeven,
        help='Whether first page is odd (as in the screen on "facing pages"), '\
             'or even (as in a book)')

    def_blankfirst = config.getValue("general", "blank_first_page", False)
    parser.add_option('--blank-first-page', dest='blank_first_page',
        action='store_true', default=def_blankfirst,
        help='Add a blank page at the beginning of the document.')

    def_breakside = config.getValue("general", "break_side", 'any')
    parser.add_option('--break-side', dest='breakside', metavar='VALUE',
        default=def_breakside,
        help='How section breaks work. Can be "even", and sections start in an even page,'\
        '"odd", and sections start in odd pages, or "any" and sections start in the next page,'\
        'be it even or odd. See also the -b option.')

    parser.add_option('--date-invariant', dest='invariant', 
        action='store_true', default=False,
        help="Don't store the current date in the PDF. Useful mainly for the test suite, "\
        "where we don't want the PDFs to change.")

    return parser

def main(args=None):
    """Parse command line and call createPdf with the correct data."""

    parser = parse_commandline()
    options, args = parser.parse_args(copy(args))

    if options.configfile:
        options.cfname=options.configfile
        parser = parse_commandline()
        options, args = parser.parse_args(copy(args))

    if options.version:
        from rst2pdf import version
        print version
        sys.exit(0)

    if options.quiet:
        log.setLevel(logging.CRITICAL)

    if options.verbose:
        log.setLevel(logging.INFO)

    if options.vverbose:
        log.setLevel(logging.DEBUG)

    if options.printssheet:
        print open(join(abspath(dirname(__file__)),
            'styles', 'styles.json')).read()
        sys.exit(0)

    filename = False

    if len(args) == 0 or args[0] == '-':
        infile = sys.stdin
        basedir=os.getcwd()
    elif len(args) > 1:
        log.critical('Usage: %s file.txt [ -o file.pdf ]', sys.argv[0])
        sys.exit(1)
    else:
        filename = args[0]
        basedir=os.path.dirname(os.path.abspath(filename))
        infile = open(filename)

    if options.output:
        outfile = options.output
        if outfile == '-':
            outfile = sys.stdout
            options.compressed = False
            #we must stay quiet
            log.setLevel(logging.CRITICAL)
    else:
        if filename:
            if filename.endswith('.txt') or filename.endswith('.rst'):
                outfile = filename[:-4] + '.pdf'
            else:
                outfile = filename + '.pdf'
        else:
            outfile = sys.stdout
            options.compressed = False
            #we must stay quiet
            log.setLevel(logging.CRITICAL)
            #/reportlab/pdfbase/pdfdoc.py output can
            #be a callable (stringio, stdout ...)

    ssheet = []
    if options.style:
        for l in options.style:
            ssheet += l.split(',')
    else:
        ssheet = []
    ssheet = [x for x in ssheet if x]

    fpath = []
    if options.fpath:
        fpath = options.fpath.split(os.pathsep)
    if options.ffolder:
        fpath.append(options.ffolder)

    spath = []
    if options.stylepath:
        spath = options.stylepath.split(os.pathsep)

    if reportlab.Version < '2.3':
        log.warning('You are using Reportlab version %s.'\
            ' The suggested version '\
            'is 2.3 or higher'%reportlab.Version)

    if options.invariant:
        patch_PDFDate()

    RstToPdf(
        stylesheets=ssheet,
        language=options.language,
        header=options.header, footer=options.footer,
        inlinelinks=options.inlinelinks,
        breaklevel=int(options.breaklevel),
        baseurl=options.baseurl,
        fit_mode=options.fit_mode,
        smarty=str(options.smarty),
        font_path=fpath,
        style_path=spath,
        repeat_table_rows=options.repeattablerows,
        footnote_backlinks=options.footnote_backlinks,
        inline_footnotes=options.inline_footnotes,
        def_dpi=int(options.def_dpi),
        basedir=basedir,
        show_frame=options.show_frame,
        splittables=options.splittables,
        blank_first_page=options.blank_first_page,
        breakside=options.breakside
        ).createPdf(text=infile.read(),
                    source_path=infile.name,
                    output=outfile,
                    compressed=options.compressed)


def patch_PDFDate():
    '''Patch reportlab.pdfdoc.PDFDate so the invariant dates work correctly'''
    from reportlab.pdfbase import pdfdoc
    class PDFDate:
        __PDFObject__ = True
        # gmt offset now suppported
        def __init__(self, invariant=True, dateFormatter=None):
            now = (2000,01,01,00,00,00,0)
            self.date = now[:6]
            self.dateFormatter = dateFormatter

        def format(self, doc):
            from time import timezone
            dhh, dmm = timezone // 3600, (timezone % 3600) % 60
            dfmt = self.dateFormatter or (
                    lambda yyyy,mm,dd,hh,m,s:
                        "D:%04d%02d%02d%02d%02d%02d%+03d'%02d'" % (yyyy,mm,dd,hh,m,s,0,0))
            return pdfdoc.format(pdfdoc.PDFString(dfmt(*self.date)), doc)
        
    pdfdoc.PDFDate = PDFDate

if __name__ == "__main__":
    main(sys.argv[1:])
