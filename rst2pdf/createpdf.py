# -*- coding: utf-8 -*-

# $URL$
# $Date$
# $Revision$

# See LICENSE.txt for licensing terms

# Some fragments of code are copied from Reportlab under this license:
#
###############################################################################
#
#   Copyright (c) 2000-2008, ReportLab Inc.
#   All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the company nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#   ARE DISCLAIMED. IN NO EVENT SHALL THE OFFICERS OR CONTRIBUTORS BE LIABLE
#   FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#   DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#   CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#   OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
#   DAMAGE.
#
###############################################################################

import argparse
import copy
import importlib
import logging
import os
import os.path
import string
import sys
import urllib.parse as urllib_parse

import docutils.core
import docutils.nodes
import docutils.readers.doctree

from docutils.parsers.rst import directives
from docutils.readers import standalone
from docutils.transforms import Transform
from docutils.utils.roman import toRoman

from reportlab.lib.units import cm

from reportlab.platypus import (
    ActionFlowable,
    BaseDocTemplate,
    Flowable,
    ImageAndFlowables,
    PageBreak,
    PageTemplate,
    TableStyle,
)

# Private functions used from these
from reportlab.platypus import doctemplate, flowables as reportlab_flowables

# TODO: Use Attrs instead of _str_attr_to_int
from smartypants import smartypants, _str_attr_to_int

from rst2pdf import (
    config,
    counter_role,
    flowables,
    oddeven_directive,
    pygments_code_block_directive,
    styles as sty,
)

# Import so that the directive is registered
import rst2pdf.aafigure_directive

from rst2pdf.flowables import (  # our own reportlab flowables
    BoundByWidth,
    BoxedContainer,
    DelayedTable,
    FrameCutter,
    Heading,
    MyIndenter,
    MyPageBreak,
    MySpacer,
    MyTableOfContents,
    OddEven,
    PageCounter,
    Reference,
    ResetNextTemplate,
    Separation,
    SetNextTemplate,
    Sidebar,
    SmartFrame,
    SplitTable,
    TocEntry,
    Transition,
    XXPreformatted,
)
from rst2pdf.image import MyImage, missing
from rst2pdf.languages import get_language_available
from rst2pdf.log import log, nodeid
from rst2pdf.opt_imports import (
    Paragraph,
    BaseHyphenator,
    PyHyphenHyphenator,
    DCWHyphenator,
    sphinx as sphinx_module,
    wordaxe
)
from rst2pdf.nodehandlers import nodehandlers
from rst2pdf.sinker import Sinker

# Small template engine for covers
# The obvious import doesn't work for complicated reasons ;-)
import tenjin
to_str = tenjin.helpers.generate_tostrfunc('utf-8')
escape = tenjin.helpers.escape
templateEngine = tenjin.Engine()


def renderTemplate(tname, **context):
    context['to_str'] = to_str
    context['escape'] = escape
    return templateEngine.render(tname, context)


numberingstyles = {
    'arabic': 'ARABIC',
    'roman': 'ROMAN_UPPER',
    'lowerroman': 'ROMAN_LOWER',
    'alpha': 'LETTERS_UPPER',
    'loweralpha':  'LETTERS_LOWER'
}


class RstToPdf(object):

    def __init__(self,
                 stylesheets=None,
                 language='en_US',
                 header=None,
                 footer=None,
                 inlinelinks=False,
                 breaklevel=1,
                 font_path=None,
                 style_path=None,
                 fit_mode='shrink',
                 background_fit_mode='center',
                 sphinx=False,
                 smarty='0',
                 baseurl=None,
                 repeat_table_rows=False,
                 footnote_backlinks=True,
                 inline_footnotes=False,
                 real_footnotes=False,
                 default_dpi=300,
                 show_frame=False,
                 highlightlang='python',  # this one is only used by Sphinx
                 basedir=os.getcwd(),
                 splittables=False,
                 blank_first_page=False,
                 first_page_on_right=False,
                 breakside='odd',
                 custom_cover='cover.tmpl',
                 floating_images=False,
                 numbered_links=False,
                 section_header_depth=2,
                 raw_html=False,
                 strip_elements_with_classes=None
                 ):
        self.debugLinesPdf = False
        self.depth = 0
        self.breakside = breakside
        self.first_page_on_right = first_page_on_right
        self.blank_first_page = blank_first_page
        self.splittables = splittables
        self.basedir = basedir
        self.language, self.docutils_language = get_language_available(
            language)[:2]
        self.doc_title = ""
        self.doc_title_clean = ""
        self.doc_subtitle = ""
        self.doc_author = ""
        self.header = header
        self.footer = footer
        self.custom_cover = custom_cover
        self.floating_images = floating_images
        self.decoration = {
            'header': header,
            'footer': footer,
            'endnotes': [],
            'extraflowables': []
        }
        # find base path
        if hasattr(sys, 'frozen'):
            self.PATH = os.path.abspath(os.path.dirname(sys.executable))
        else:
            self.PATH = os.path.abspath(os.path.dirname(__file__))

        self.font_path = font_path or []
        self.style_path = style_path or []
        self.default_dpi = default_dpi
        self.loadStyles(stylesheets or [])

        self.docutils_languages = {}
        self.inlinelinks = inlinelinks
        self.breaklevel = breaklevel
        self.fit_mode = fit_mode
        self.background_fit_mode = background_fit_mode
        self.to_unlink = []
        self.smarty = smarty
        self.baseurl = baseurl
        self.repeat_table_rows = repeat_table_rows
        self.footnote_backlinks = footnote_backlinks
        self.inline_footnotes = inline_footnotes
        self.real_footnotes = real_footnotes
        # Real footnotes are always a two-pass thing.
        if self.real_footnotes:
            self.mustMultiBuild = True
        self.default_dpi = default_dpi
        self.show_frame = show_frame
        self.numbered_links = numbered_links
        self.section_header_depth = section_header_depth
        self.img_dir = os.path.join(self.PATH, 'images')
        self.raw_html = raw_html
        self.strip_elements_with_classes = strip_elements_with_classes or []

        # Sorry about this, but importing sphinx.roles makes some
        # ordinary documents fail (demo.txt specifically) so
        # I can' t just try to import it outside. I need
        # to do it only if it's requested
        if sphinx and sphinx_module:
            import sphinx.roles
            from .sphinxnodes import sphinxhandlers
            self.highlightlang = highlightlang
            self.gen_pdftext, self.gen_elements = sphinxhandlers(self)
        else:
            # These rst2pdf extensions conflict with sphinx
            directives.register_directive(
                'code-block',
                pygments_code_block_directive.code_block_directive
            )
            directives.register_directive(
                'code',
                pygments_code_block_directive.code_block_directive
            )
            self.gen_pdftext, self.gen_elements = nodehandlers(self)

        self.sphinx = sphinx

        if not self.styles.languages:
            self.styles.languages = []
            if self.language:
                self.styles.languages.append(self.language)
                self.styles['bodytext'].language = self.language
            else:
                self.styles.languages.append('en_US')
                self.styles['bodytext'].language = 'en_US'
        # Load the docutils language modules for all required languages
        for lang in self.styles.languages:
            self.docutils_languages[lang] = get_language_available(lang)[2]

        # Load the hyphenators for all required languages
        if wordaxe is not None:
            for lang in self.styles.languages:
                if lang.split('_', 1)[0] == 'de':
                    try:
                        wordaxe.hyphRegistry[lang] = DCWHyphenator('de', 5)
                        continue
                    except Exception:
                        # hyphenators may not always be available or crash,
                        # e.g. wordaxe issue 2809074 (http://is.gd/16lqs)
                        log.warning("Can't load wordaxe DCW hyphenator for" +
                                    " German language, trying Py hyphenator" +
                                    " instead")
                    else:
                        continue
                try:
                    wordaxe.hyphRegistry[lang] = PyHyphenHyphenator(lang)
                except Exception:
                    log.warning("Can't load wordaxe Py hyphenator for" +
                                " language %s, trying base hyphenator", lang)
                else:
                    continue
                try:
                    wordaxe.hyphRegistry[lang] = BaseHyphenator(lang)
                except Exception:
                    log.warning("Can't even load wordaxe base hyphenator")
            log.info('hyphenation by default in %s , loaded %s',
                     self.styles['bodytext'].language,
                     ','.join(self.styles.languages))

        self.pending_targets = []
        self.targets = []

    def loadStyles(self, styleSheets=None):

        if styleSheets is None:
            styleSheets = []

        self.styles = sty.StyleSheet(styleSheets,
                                     self.font_path,
                                     self.style_path,
                                     def_dpi=self.default_dpi)

    def style_language(self, style):
        """
        Return language corresponding to this style.
        """
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
        """
        Translate text for label.
        """
        try:
            text = self.docutils_languages[
                        self.style_language(style)].labels[label]
        except KeyError:
            text = label.capitalize()
        return text

    def text_for_bib_field(self, field, style):
        """
        Translate text for bibliographic fields.
        """
        try:
            text = self.docutils_languages[
                        self.style_language(style)].bibliographic_fields[field]
        except KeyError:
            text = field
        return text + ":"

    def author_separator(self, style):
        """
        Return separator string for authors.
        """
        try:
            sep = self.docutils_languages[
                    self.style_language(style)].author_separators[0]
        except KeyError:
            sep = ';'
        return sep + " "

    def styleToTags(self, style):
        """
        Take a style name and return a pair of opening/closing tags for it

        For example, "<font face=helvetica size=14 color=red>". Used for inline
        nodes (custom interpreted roles).
        """
        try:
            s = self.styles[style]
            r1 = ['<font face="%s" color="#%s" ' %
                  (s.fontName, s.textColor.hexval()[2:])]
            bc = s.backColor
            if bc:
                r1.append('backColor="#%s"' % bc.hexval()[2:])
            if s.trueFontSize:
                r1.append('size="%d"' % s.fontSize)
            r1.append('>')
            r2 = ['</font>']

            if s.strike:
                r1.append('<strike>')
                r2.insert(0, '</strike>')
            if s.underline:
                r1.append('<u>')
                r2.insert(0, '</u>')

            return [''.join(r1), ''.join(r2)]
        except KeyError:
            log.warning('Unknown class %s', style)
            return None

    def styleToFont(self, style):
        """
        Take a style name and return a font tag for it.

        For example, "<font face=helvetica size=14 color=red>". Used for inline
        nodes (custom interpreted roles).
        """
        try:
            s = self.styles[style]
            r = ['<font face="%s" color="#%s" ' %
                 (s.fontName, s.textColor.hexval()[2:])]
            bc = s.backColor
            if bc:
                r.append('backColor="#%s"' % bc.hexval()[2:])
            if s.trueFontSize:
                r.append('size="%d"' % s.fontSize)
            r.append('>')
            return ''.join(r)
        except KeyError:
            log.warning('Unknown class %s', style)
            return None

    def gather_pdftext(self, node, replaceEnt=True):
        return ''.join([self.gen_pdftext(n, replaceEnt)
                        for n in node.children])

    def gather_elements(self, node, style=None):
        if style is None:
            style = self.styles.styleForNode(node)
        r = []
        if 'float' in style.__dict__:
            style = None  # Don't pass floating styles to children!
        for n in node.children:
            # import pdb; pdb.set_trace()
            r.extend(self.gen_elements(n, style=style))
        return r

    def bullet_for_node(self, node):
        """
        Take a node, assume it's some sort of item whose parent is a list,
        and return the bullet text it should have.
        """
        b = ""
        t = 'item'
        if node.parent.get('start'):
            start = int(node.parent.get('start'))
        else:
            start = 1

        if node.parent.get('bullet') or isinstance(
                node.parent, docutils.nodes.bullet_list):
            b = node.parent.get('bullet', '*')
            if b == "None":
                b = ""
            t = 'bullet'
        elif node.parent.get('enumtype') == 'arabic':
            b = str(node.parent.children.index(node) + start) + '.'
        elif node.parent.get('enumtype') == 'lowerroman':
            b = toRoman(node.parent.children.index(node) + start).lower() + '.'
        elif node.parent.get('enumtype') == 'upperroman':
            b = toRoman(node.parent.children.index(node) + start).upper() + '.'
        elif node.parent.get('enumtype') == 'loweralpha':
            b = string.ascii_lowercase[node.parent.children.index(node) +
                                       start - 1] + '.'
        elif node.parent.get('enumtype') == 'upperalpha':
            b = string.ascii_uppercase[node.parent.children.index(node) +
                                       start - 1] + '.'
        else:
            log.critical("Unknown kind of list_item %s [%s]",
                         node.parent, nodeid(node))
        return b, t

    def filltable(self, rows):
        """
        Take a list of rows consisting of cells and perform the following fixes

          * For multicolumn cells, add continuation cells to make all rows the
            same size. These cells have to be multirow if the original cell is
            multirow.

          * For multirow cell, insert continuation cells, to make all columns
            the same size.

          * If there are still shorter rows, add empty cells at the end (ReST
            quirk)

          * Once the table is *normalized*, create spans list, fitting for
            reportlab's Table class.
        """
        # If there is a multicol cell, we need to insert Continuation Cells
        # to make all rows the same length
        for y in range(0, len(rows)):
            for x in range(len(rows[y]) - 1, -1, -1):
                cell = rows[y][x]
                if isinstance(cell, str):
                    continue
                if cell.get("morecols"):
                    for i in range(0, cell.get("morecols")):
                        e = docutils.nodes.entry("")
                        e["morerows"] = cell.get("morerows", 0)
                        rows[y].insert(x + 1, e)

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
        """
        Preformatted section that gets horizontally compressed if needed.
        """
        # Pass a ridiculous size, then it will shrink to what's available
        # in the frame
        return BoundByWidth(
            2000 * cm,
            content=[XXPreformatted(text, style)],
            mode=self.fit_mode,
            style=style
        )

    def createPdf(self, text=None,
                  source_path=None,
                  output=None,
                  doctree=None,
                  compressed=False,
                  # This adds entries to the PDF TOC
                  # matching the rst source lines
                  debugLinesPdf=False):
        """
        Create a PDF from text or doctree and save it in outfile.

        Input is either text (ReST) or a doctree (docutil nodes)
        If outfile is a string, it's a filename.  If it's something with a
        write method, (like a StringIO, or a file object), the data is
        saved there.
        """
        self.decoration = {
            'header': self.header,
            'footer': self.footer,
            'endnotes': [],
            'extraflowables': [],
        }

        self.pending_targets = []
        self.targets = []
        self.debugLinesPdf = debugLinesPdf

        if doctree is None:
            if text is not None:
                if self.language:
                    settings_overrides = {
                        'language_code': self.docutils_language
                    }
                else:
                    settings_overrides = {}
                settings_overrides['strip_elements_with_classes'] = \
                    self.strip_elements_with_classes
                self.doctree = docutils.core.publish_doctree(
                    text,
                    source_path=source_path,
                    settings_overrides=settings_overrides
                )
                log.debug(self.doctree)
            else:
                log.error('Error: createPdf needs a text or a doctree')
                return 2
        else:
            self.doctree = doctree

        # TODO: Why are we importing here?
        if self.numbered_links:
            # Transform all links to sections so they show numbers
            from rst2pdf.sectnumlinks import SectNumFolder, SectRefExpander
            snf = SectNumFolder(self.doctree)
            self.doctree.walk(snf)
            srf = SectRefExpander(self.doctree, snf.sectnums)
            self.doctree.walk(srf)
        if self.strip_elements_with_classes:
            from docutils.transforms.universal import StripClassesAndElements
            sce = StripClassesAndElements(self.doctree)
            sce.apply()

        elements = self.gen_elements(self.doctree)

        # Find cover template, save it in cover_file
        def find_cover(name):
            cover_path = [
                self.basedir,
                os.path.expanduser('~/.rst2pdf'),
                os.path.join(self.PATH, 'templates')
            ]
            cover_file = None
            for d in cover_path:
                if os.path.exists(os.path.join(d, name)):
                    cover_file = os.path.join(d, name)
                    break
            return cover_file

        cover_file = find_cover(self.custom_cover)
        if cover_file is None:
            log.error("Can't find cover template %s, using default"
                      % self.custom_cover)
            cover_file = find_cover('cover.tmpl')

        # Feed data to the template, get restructured text.
        cover_text = renderTemplate(
            tname=cover_file,
            title=self.doc_title,
            subtitle=self.doc_subtitle
        )

        # This crashes sphinx because .. class:: in sphinx is
        # something else. Ergo, pdfbuilder does it in its own way.
        if not self.sphinx:
            elements = self.gen_elements(
                publish_secondary_doctree(cover_text, self.doctree,
                                          source_path)
            ) + elements

        if self.blank_first_page:
            elements.insert(0, PageBreak())

        # Put the endnotes at the end ;-)
        endnotes = self.decoration['endnotes']
        if endnotes:
            elements.append(MySpacer(1, 2 * cm))
            elements.append(Separation())
            for n in self.decoration['endnotes']:
                t_style = TableStyle(self.styles['endnote'].commands)
                colWidths = self.styles['endnote'].colWidths
                elements.append(DelayedTable([[n[0], n[1]]],
                                style=t_style, colWidths=colWidths))

        if self.floating_images:
            # Handle images with alignment more like in HTML
            new_elem = []
            for e in elements[::-1]:
                if (
                    isinstance(e, MyImage) and
                    e.image.hAlign != 'CENTER' and
                    new_elem
                ):
                    # This is an image where flowables should wrap
                    # around it
                    popped = new_elem.pop()
                    new_elem.append(ImageAndFlowables(e, popped,
                                    imageSide=e.image.hAlign.lower()))
                else:
                    new_elem.append(e)

            elements = new_elem
            elements.reverse()

        head = self.decoration['header']
        foot = self.decoration['footer']

        # So, now, create the FancyPage with the right sizes and elements
        FP = FancyPage("fancypage", head, foot, self)

        pdfdoc = FancyDocTemplate(
            output,
            pageTemplates=[FP],
            pagesize=self.styles.ps,
            title=self.doc_title_clean,
            author=self.doc_author,
            pageCompression=compressed,
        )
        pdfdoc.client = self

        if getattr(self, 'mustMultiBuild', False):
            # Force a multibuild pass
            if not isinstance(elements[-1], UnhappyOnce):
                log.info('Forcing second pass so Total pages work')
                elements.append(UnhappyOnce())
        while True:
            try:
                log.info("Starting build")
                # See if this *must* be multipass
                pdfdoc.multiBuild(elements)
                # Force a multibuild pass

                # FIXME: since mustMultiBuild is set by the
                # first pass in the case of ###Total###, then we
                # make a new forced two-pass build. This is broken.
                # conceptually.

                if getattr(self, 'mustMultiBuild', False):
                    # Force a multibuild pass
                    if not isinstance(elements[-1], UnhappyOnce):
                        log.info('Forcing second pass so Total pages work')
                        elements.append(UnhappyOnce())
                        continue
                # # Rearrange footnotes if needed
                if self.real_footnotes:
                    newStory = []
                    fnPile = []
                    for e in elements:
                        if getattr(e, 'isFootnote', False):
                            # Add it to the pile
                            # if not isinstance (e, MySpacer):
                            fnPile.append(e)
                        elif getattr(e, '_atTop', False) or isinstance(
                                e, (UnhappyOnce, MyPageBreak)):
                            if fnPile:
                                fnPile.insert(0, Separation())
                                newStory.append(Sinker(fnPile))
                            newStory.append(e)
                            fnPile = []
                        else:
                            newStory.append(e)
                    elements = newStory + fnPile
                    for e in elements:
                        if hasattr(e, '_postponed'):
                            delattr(e, '_postponed')
                    self.real_footnotes = False
                    continue
                break
            except ValueError as v:
                # FIXME: cross-document links come through here, which means
                # an extra pass per cross-document reference. Which sucks.
                # if v.args and str(v.args[0]).startswith('format not resolved'):
                    # missing=str(v.args[0]).split(' ')[-1]
                    # log.error('Adding missing reference to %s and rebuilding. This is slow!'%missing)
                    # elements.append(Reference(missing))
                    # for e in elements:
                        # if hasattr(e,'_postponed'):
                            # delattr(e,'_postponed')
                # else:
                    # raise
                raise

        # doc = SimpleDocTemplate("phello.pdf")
        # doc.build(elements)
        for fn in self.to_unlink:
            try:
                os.unlink(fn)
            except OSError:
                pass
        return 0


class FancyDocTemplate(BaseDocTemplate):

    def afterFlowable(self, flowable):
        if isinstance(flowable, Heading):
            # Notify TOC entry for headings/abstracts/dedications.
            level, text = flowable.level, flowable.text
            parent_id = flowable.parent_id
            node = flowable.node
            pagenum = setPageCounter()
            self.notify('TOCEntry', (level, text, pagenum, parent_id, node))

def setPageCounter(counter=None, style=None):
    if counter is not None:
        PageCounter.counter = counter
    if style is not None:
        PageCounter.counterStyle = style

    if PageCounter.counterStyle == 'lowerroman':
        ptext = toRoman(PageCounter.counter).lower()
    elif PageCounter.counterStyle == 'roman':
        ptext = toRoman(PageCounter.counter).upper()
    elif PageCounter.counterStyle == 'alpha':
        ptext = string.ascii_uppercase[PageCounter.counter % 26]
    elif PageCounter.counterStyle == 'loweralpha':
        ptext = string.ascii_lowercase[PageCounter.counter % 26]
    else:
        ptext = str(PageCounter.counter)
    return ptext


class MyContainer(reportlab_flowables._Container, Flowable):
    pass


class UnhappyOnce(doctemplate.IndexingFlowable):

    """
    An indexing flowable that is only unsatisfied once.
    If added to a story, it will make multiBuild run
    at least two passes. Useful for ###Total###
    """

    _unhappy = True

    def isSatisfied(self):
        if self._unhappy:
            self._unhappy = False
            return False
        return True

    def draw(self):
        pass


class HeaderOrFooter(object):

    """
    A helper object for FancyPage (below)
    HeaderOrFooter handles operations which are common
    to both headers and footers
    """

    def __init__(self, items=None, isfooter=False, client=None):
        self.items = items
        if isfooter:
            locinfo = 'footer showFooter defaultFooter footerSeparator'
        else:
            locinfo = 'header showHeader defaultHeader headerSeparator'
        self.isfooter = isfooter
        self.loc, self.showloc, self.defaultloc, self.addsep = locinfo.split()
        self.totalpages = 0
        self.client = client

    def prepare(self, pageobj, canv, doc):
        showloc = pageobj.template.get(self.showloc, True)
        height = 0
        items = self.items
        if showloc:
            if not items:
                items = pageobj.template.get(self.defaultloc)
                if items:
                    items = self.client.gen_elements(publish_secondary_doctree(items, self.client.doctree, None))
            if items:
                if isinstance(items, list):
                    items = items[:]
                else:
                    items = [Paragraph(items, pageobj.styles[self.loc])]
                addsep = pageobj.template.get(self.addsep, False)
                if addsep:
                    if self.isfooter:
                        items.insert(0, Separation())
                    else:
                        items.append(Separation())
                _, height = reportlab_flowables._listWrapOn(items, pageobj.tw, canv)
        self.prepared = height and items
        return height

    def replaceTokens(self, elems, canv, doc, smarty):
        """
        Put doc_title/page number/etc in text of header/footer.
        """
        # Make sure page counter is up to date
        pnum = setPageCounter()

        def replace(text):
            if not isinstance(text, str):
                try:
                    text = str(text, e.encoding)
                except AttributeError:
                    text = str(text, 'utf-8')
                except TypeError:
                    text = str(text, 'utf-8')

            text = text.replace('###Page###', pnum)
            if '###Total###' in text:
                text = text.replace('###Total###', str(self.totalpages))
                self.client.mustMultiBuild = True
            text = text.replace("###Title###", doc.title)
            text = text.replace("###Section###",
                                getattr(canv, 'sectName', ''))
            text = text.replace("###SectNum###",
                                getattr(canv, 'sectNum', ''))
            smartyattr = _str_attr_to_int(smarty)
            text = smartypants(text, smartyattr)
            return text

        for i, e in enumerate(elems):
            # TODO: implement a search/replace for arbitrary things
            if isinstance(e, Paragraph):
                text = replace(e.text)
                elems[i] = Paragraph(text, e.style)
            elif isinstance(e, DelayedTable):
                data = copy.deepcopy(e.data)
                for r, row in enumerate(data):
                    for c, cell in enumerate(row):
                        if isinstance(cell, list):
                            data[r][c] = self.replaceTokens(cell, canv, doc, smarty)
                        else:
                            row[r] = self.replaceTokens([cell, ], canv, doc, smarty)[0]
                elems[i] = DelayedTable(data, e._colWidths, e.style)

            elif isinstance(e, BoundByWidth):
                for index, item in enumerate(e.content):
                    if isinstance(item, Paragraph):
                        e.content[index] = Paragraph(replace(item.text), item.style)
                elems[i] = e

            elif isinstance(e, OddEven):
                odd = self.replaceTokens([e.odd, ], canv, doc, smarty)[0]
                even = self.replaceTokens([e.even, ], canv, doc, smarty)[0]
                elems[i] = OddEven(odd, even)
        return elems

    def draw(self, pageobj, canv, doc, x, y, width, height):
        self.totalpages = max(self.totalpages, doc.page)
        items = self.prepared
        if items:
            self.replaceTokens(items, canv, doc, pageobj.smarty)
            container = MyContainer()
            container._content = items
            container.width = width
            container.height = height
            container.drawOn(canv, x, y)


class FancyPage(PageTemplate):

    """
    A page template that handles changing layouts.
    """

    def __init__(self, _id, _head, _foot, client):
        self.client = client
        self.styles = client.styles
        self._head = HeaderOrFooter(_head, client=client)
        self._foot = HeaderOrFooter(_foot, True, client)
        self.smarty = client.smarty
        self.show_frame = client.show_frame
        self.image_cache = {}
        super().__init__(_id, [])

    def draw_background(self, which, canv):
        """
        Draw a background and/or foreground image on each page.

        The image is calculate once, cached, and reused on every page
        in the template.

        How the background is drawn depends on the
        --fit-background-mode option.

        If desired, we could add code to push it around on the page, using
        stylesheets to align and/or set the offset.
        """
        uri = self.template[which]
        info = self.image_cache.get(uri)
        if info is None:
            fname, _, _ = MyImage.split_uri(uri)
            if not os.path.exists(fname):
                del self.template[which]
                log.error("Missing %s image file: %s", which, uri)
                return
            try:
                w, h, kind = MyImage.size_for_node(dict(uri=uri,), self.client)
            except ValueError:
                # Broken image, return arbitrary stuff
                uri = missing
                w, h, kind = 100, 100, 'direct'

            pw, ph = self.styles.pw, self.styles.ph
            if self.client.background_fit_mode == 'center':
                scale = min(1.0, 1.0 * pw / w, 1.0 * ph / h)
                sw, sh = w * scale, h * scale
                x, y = (pw - sw) / 2.0, (ph - sh) / 2.0
            elif self.client.background_fit_mode == 'scale':
                x, y = 0, 0
                sw, sh = pw, ph
            else:
                log.error('Unknown background fit mode: %s' %
                          self.client.background_fit_mode)
                # Do scale anyway
                x, y = 0, 0
                sw, sh = pw, ph

            bg = MyImage(uri, sw, sh, client=self.client)
            self.image_cache[uri] = info = bg, x, y
        bg, x, y = info
        bg.drawOn(canv, x, y)

    def is_left(self, page_num):
        """
        Default behavior is that the first page is on the left.

        If the user has --first_page_on_right, the calculation is reversed.
        """
        val = page_num % 2 == 1
        if self.client.first_page_on_right:
            val = not val
        return val

    def beforeDrawPage(self, canv, doc):
        """
        Do adjustments to the page according to where we are in the document.

        Gutter margins on left or right as needed
        """
        styles = self.styles
        self.tw = styles.pw - styles.lm - styles.rm - styles.gm
        # What page template to use?
        tname = canv.__dict__.get('templateName',
                                  self.styles.firstTemplate)
        self.template = self.styles.pageTemplates[tname]
        canv.templateName = tname

        doct = getattr(canv, '_doctemplate', None)
        canv._doctemplate = None  # to make _listWrapOn work

        if doc.page == 1:
            PageCounter.counter = 0
            PageCounter.counterStyle = 'arabic'
        PageCounter.counter += 1

        # Adjust text space accounting for header/footer

        self.hh = self._head.prepare(self, canv, doc)
        self.fh = self._foot.prepare(self, canv, doc)

        canv._doctemplate = doct

        self.hx = styles.lm
        self.hy = styles.ph - styles.tm - self.hh

        self.fx = styles.lm
        self.fy = styles.bm
        self.th = styles.ph - styles.tm - styles.bm - self.hh - \
            self.fh - styles.ts - styles.bs

        # Adjust gutter margins
        if self.is_left(doc.page):  # Left page
            x1 = styles.lm
        else:  # Right page
            x1 = styles.lm + styles.gm
        y1 = styles.bm + self.fh + styles.bs

        # If there is a background parameter for this page Template, draw it
        if 'background' in self.template:
            self.draw_background('background', canv)

        self.frames = []
        for frame in self.template['frames']:
            self.frames.append(SmartFrame(
                self,
                styles.adjustUnits(frame[0], self.tw) + x1,
                styles.adjustUnits(frame[1], self.th) + y1,
                styles.adjustUnits(frame[2], self.tw),
                styles.adjustUnits(frame[3], self.th),
                showBoundary=self.show_frame
            ))
        canv.firstSect = True
        canv._pagenum = doc.page
        for frame in self.frames:
            frame._pagenum = doc.page

    def afterDrawPage(self, canv, doc):
        """
        Draw header/footer.
        """
        # Adjust for gutter margin
        canv.addPageLabel(canv._pageNumber - 1, numberingstyles[PageCounter.counterStyle],
                          PageCounter.counter)

        log.info('Page %s [%s]' % (PageCounter.counter, doc.page))
        if self.is_left(doc.page):  # Left page
            hx = self.hx
            fx = self.fx
        else:  # Right Page
            hx = self.hx + self.styles.gm
            fx = self.fx + self.styles.gm

        self._head.draw(self, canv, doc, hx, self.hy, self.tw, self.hh)
        self._foot.draw(self, canv, doc, fx, self.fy, self.tw, self.fh)

        # If there is a foreground parameter for this page Template, draw it
        if 'foreground' in self.template:
            self.draw_background('foreground', canv)


def parse_commandline():
    # Get defaults from config.
    # First, the names and default values to get from the config
    d = {
        'stylesheets': '',
        'stylesheet_path': '',
        'compressed': False,
        'font_path': '',
        'language': 'en_US',
        'header': None,
        'footer': None,
        'section_header_depth': 2,
        'smartquotes': '0',
        'fit_mode': 'shrink',
        'numbered_links': False,
        'floating_images': False,
        'break_level': 0,
        'blank_first_page': False,
        'first_page_on_right': False,
        'background_fit_mode': 'center',
        'raw_html': False,
        'footnote_backlinks': True,
        'inline_footnotes': False,
        'real_footnotes': False,
        'default_dpi': 300,
        'break_side': 'any',
        'custom_cover': 'cover.tmpl',
    }
    # Get values from the config
    d = {k: config.getValue('general', k, v) for k, v in d.items()}
    # Now add/change the exceptions
    d['stylesheets'] = ','.join(
        os.path.expanduser(p) for p in d['stylesheets'].split(',')
    )
    d['stylesheet_path'] = os.pathsep.join(
        os.path.expanduser(p) for p in d['stylesheet_path'].split(os.pathsep)
    )
    d['font_path'] = os.pathsep.join(
        os.path.expanduser(p) for p in d['font_path'].split(os.pathsep)
    )
    d['baseurl'] = urllib_parse.urlunparse(
        ['file', os.getcwd() + os.sep, '', '', '', '']
    )

    # Set up the parser
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--config',
        dest='configfile',
        metavar='FILE',
        help='Config file to use. Default=~/.rst2pdf/config'
    )

    parser.add_argument(
        '-o',
        '--output',
        metavar='FILE',
        help='Write the PDF to FILE'
    )

    parser.add_argument(
        '-s',
        '--stylesheets',
        dest='style',
        action='append',
        metavar='STYLESHEETS',
        default=[d['stylesheets']],
        help='A comma-separated list of custom stylesheets. Default="%s"' %
             d['stylesheets']
    )

    parser.add_argument(
        '--stylesheet-path',
        dest='stylepath',
        metavar='FOLDER%sFOLDER%s...%sFOLDER' % ((os.pathsep,) * 3),
        default=d['stylesheet_path'],
        help='A list of folders to search for stylesheets, separated ' +
             'using "%s". Default="%s"' % (os.pathsep, d['stylesheet_path'])
    )

    parser.add_argument(
        '-c',
        '--compressed',
        action="store_true",
        default=d['compressed'],
        help='Create a compressed PDF. Default=%s' % d['compressed']
    )

    parser.add_argument(
        '--print-stylesheet',
        dest='printssheet',
        action="store_true",
        default=False,
        help='Print the default stylesheet and exit'
    )

    parser.add_argument(
        '--font-folder',
        dest='ffolder',
        metavar='FOLDER',
        help='Search this folder for fonts. (Deprecated)'
    )

    parser.add_argument(
        '--font-path',
        dest='font_path',
        metavar='FOLDER%sFOLDER%s...%sFOLDER' % ((os.pathsep,) * 3),
        default=d['font_path'],
        help='A list of folders to search for fonts, separated using' +
             '"%s". Default="%s"' % (os.pathsep, d['font_path'])
    )

    parser.add_argument(
        '--baseurl',
        dest='baseurl',
        metavar='URL',
        default=d['baseurl'],
        help='The base URL for relative URLs. Default="%s"' % d['baseurl']
    )

    parser.add_argument(
        '-l',
        '--language',
        metavar='LANG',
        default=d['language'],
        help='Language to be used for hyphenation ' +
             'and docutils localizations. Default="%s"' % d['language']
    )

    parser.add_argument(
        '--header',
        metavar='HEADER',
        default=d['header'],
        dest='header',
        help='Page header if not specified in the document. ' +
             'Default="%s"' % d['header'])

    parser.add_argument(
        '--footer',
        metavar='FOOTER',
        default=d['footer'],
        dest='footer',
        help='Page footer if not specified in the document. ' +
             'Default="%s"' % d['footer'])

    parser.add_argument(
        '--section-header-depth',
        metavar='N',
        default=d['section_header_depth'],
        dest='section_header_depth',
        help="Sections up to this depth will be used in the header and " +
             "footer's replacement of ###Section###. Default=%s" %
                d['section_header_depth']
    )

    parser.add_argument(
        "--smart-quotes",
        metavar="VALUE",
        default=d['smartquotes'],
        dest="smarty",
        help='Try to convert ASCII quotes, ellipses and dashes ' +
             'to the typographically correct equivalent. For details, ' +
             'read the man page or the manual. Default="%s"' % d['smartquotes']
    )

    parser.add_argument(
        '--fit-literal-mode',
        metavar='MODE',
        default=d['fit_mode'],
        dest='fit_mode',
        help='What to do when a literal is too wide. One of error, ' +
             'overflow, shrink, truncate. Default="%s"' % d['fit_mode']
    )

    parser.add_argument(
        '--fit-background-mode',
        metavar='MODE',
        default=d['background_fit_mode'],
        dest='background_fit_mode',
        help='How to fit the background image to the page. ' +
             'One of scale or center. Default="%s"' % d['background_fit_mode']
    )

    parser.add_argument(
        '--inline-links',
        action="store_true",
        dest='inlinelinks',
        default=False,
        help='Shows target between parentheses instead of active link.'
    )

    parser.add_argument(
        '--repeat-table-rows',
        action="store_true",
        dest='repeattablerows',
        default=False,
        help='Repeats header row for each split table.'
    )

    parser.add_argument(
        '--raw-html',
        action="store_true",
        dest='raw_html',
        default=d['raw_html'],
        help='Support embeddig raw HTML. Default=%s' % d['raw_html']
    )

    parser.add_argument(
        '-q',
        '--quiet',
        action="store_true",
        dest='quiet',
        default=False,
        help='Print less information.'
    )

    parser.add_argument(
        '-v',
        '--verbose',
        action="store_true",
        dest='verbose',
        default=False,
        help='Print debug information.'
    )

    parser.add_argument(
        '--very-verbose',
        action="store_true",
        dest='vverbose',
        default=False,
        help='Print even more debug information.'
    )

    parser.add_argument(
        '--version',
        action="store_true",
        dest='version',
        default=False,
        help='Print version number and exit.'
    )

    parser.add_argument(
        '--no-footnote-backlinks',
        action='store_false',
        dest='footnote_backlinks',
        default=d['footnote_backlinks'],
        help='Disable footnote backlinks. Default=%s' %
             str(not d['footnote_backlinks'])
    )

    parser.add_argument(
        '--inline-footnotes',
        action='store_true',
        dest='inline_footnotes',
        default=d['inline_footnotes'],
        help='Show footnotes inline. Default=%s' %
             str(not d['inline_footnotes'])
    )

    parser.add_argument(
        '--real-footnotes',
        action='store_true',
        dest='real_footnotes',
        default=d['real_footnotes'],
        help='Show footnotes at the bottom of the page where they are ' +
             'defined. Default=%s' % str(d['real_footnotes'])
    )

    parser.add_argument(
        '--default-dpi',
        dest='default_dpi',
        metavar='NUMBER',
        default=d['default_dpi'],
        help='DPI for objects sized in pixels. Default=%d' % d['default_dpi']
    )

    parser.add_argument(
        '--show-frame-boundary',
        dest='show_frame',
        action='store_true',
        default=False,
        help='Show frame borders (only useful for debugging). Default=False'
    )

    parser.add_argument(
        '--disable-splittables',
        dest='splittables',
        action='store_false',
        default=True,
        help="Don't use splittable flowables in some elements. " +
             "Only try this if you can't process a document any other way."
    )

    parser.add_argument(
        '-b',
        '--break-level',
        dest='breaklevel',
        metavar='LEVEL',
        default=d['break_level'],
        help='Maximum section level that starts in a new page. ' +
             'Default: %d' % d['break_level'])

    parser.add_argument(
        '--blank-first-page',
        dest='blank_first_page',
        action='store_true',
        default=d['blank_first_page'],
        help='Add a blank page at the beginning of the document.'
    )

    parser.add_argument(
        '--first-page-on-right',
        dest='first_page_on_right',
        action='store_true',
        default=d['first_page_on_right'],
        help='Two-sided book style (where first page starts on the right side)'
    )

    parser.add_argument(
        '--break-side',
        dest='breakside', metavar='VALUE',
        default=d['break_side'],
        help='How section breaks work. Can be "even", and sections start ' +
             'in an even page, "odd", and sections start in odd pages, ' +
             'or "any" and sections start in the next page, be it even or ' +
             'odd. See also the -b option.'
    )

    parser.add_argument(
        '--date-invariant',
        dest='invariant',
        action='store_true',
        default=False,
        help="Don't store the current date in the PDF. " +
             "Useful mainly for the test suite, " +
             "where we don't want the PDFs to change."
        )

    parser.add_argument(
        '-e',
        '--extension-module',
        dest='extensions',
        action="append",
        default=['vectorpdf'],
        help="Add a helper extension module to this invocation of rst2pdf " +
             "(module must end in .py and be on the python path)"
    )

    parser.add_argument(
        '--custom-cover',
        dest='custom_cover',
        metavar='FILE',
        default=d['custom_cover'],
        help='Template file used for the cover page. Default: %s' %
             d['custom_cover']
    )

    parser.add_argument(
        '--use-floating-images',
        action='store_true',
        default=d['floating_images'],
        dest='floating_images',
        help='Makes images with :align: attribute work more like in ' +
             'rst2html. Default: %s' % d['floating_images']
    )

    parser.add_argument(
        '--use-numbered-links',
        action='store_true',
        default=d['numbered_links'],
        dest='numbered_links',
        help='When using numbered sections, adds the numbers to all links ' +
             'referring to the section headers. Default: %s' %
                 d['numbered_links']
    )

    parser.add_argument(
        '--strip-elements-with-class',
        action='append',
        dest='strip_elements_with_classes',
        metavar='CLASS',
        help='Remove elements with this CLASS from the output. Can be used ' +
             'multiple times.'
    )

    parser.add_argument(
        'filenames',
        nargs='+',
        help='Input file (and optionally an output filename)'
    )

    return parser


def main(_args=None):
    """
    Parse command line and call createPdf with the correct data.

    The return value is the system exit code.
    """
    parser = parse_commandline()
    # Fix issue 430: don't overwrite args
    # need to parse_args to see i we have a custom config file
    args = parser.parse_args(copy.copy(_args))

    if args.configfile:
        # If there is a config file, we need to reparse
        # the command line because we have different defaults
        config.parseConfig(args.configfile)
        parser = parse_commandline()
        args = parser.parse_args(copy.copy(_args))

    if args.version:
        from rst2pdf import version
        print(version)
        return 0

    if args.quiet:
        log.setLevel(logging.CRITICAL)

    if args.verbose:
        log.setLevel(logging.INFO)

    if args.vverbose:
        log.setLevel(logging.DEBUG)

    if args.printssheet:
        # find base path
        if hasattr(sys, 'frozen'):
            PATH = os.path.abspath(os.path.dirname(sys.executable))
        else:
            PATH = os.path.abspath(os.path.dirname(__file__))
        print(open(os.path.join(PATH, 'styles', 'styles.style')).read())
        return 0

    filename = False

    if len(args.filenames) == 0:
        args.filenames = ['-', ]
    elif len(args.filenames) > 2:
        log.critical('Usage: %s [ file.txt [ file.pdf ] ]', sys.argv[0])
        return 1
    elif len(args.filenames) == 2:
        if args.output:
            log.critical('You may not give both "-o/--output" and second argument')
            return 1
        args.output = args.filenames.pop()

    if args.filenames[0] == '-':
        infile = sys.stdin
        args.basedir = os.getcwd()
    elif len(args.filenames) > 1:
        log.critical('Usage: %s file.txt [ -o file.pdf ]', sys.argv[0])
        return 1
    else:
        filename = args.filenames[0]
        args.basedir = os.path.dirname(os.path.abspath(filename))
        try:
            # TODO: Replace with a context manager
            infile = open(filename)
        except IOError as e:
            log.error(e)
            return 1
    args.infile = infile

    if args.output:
        outfile = args.output
        if outfile == '-':
            outfile = sys.stdout
            args.compressed = False
            # we must stay quiet
            log.setLevel(logging.CRITICAL)
    else:
        if filename:
            if filename.endswith('.txt') or filename.endswith('.rst'):
                outfile = filename[:-4] + '.pdf'
            else:
                outfile = filename + '.pdf'
        else:
            outfile = sys.stdout
            args.compressed = False
            # we must stay quiet
            log.setLevel(logging.CRITICAL)
            # /reportlab/pdfbase/pdfdoc.py output can
            # be a callable (stringio, stdout ...)
    args.outfile = outfile

    ssheet = []
    if args.style:
        for l in args.style:
            ssheet += l.split(',')
    else:
        ssheet = []
    args.style = [x for x in ssheet if x]

    font_path = []
    if args.font_path:
        font_path = args.font_path.split(os.pathsep)
    if args.ffolder:
        font_path.append(args.ffolder)
    args.font_path = font_path

    spath = []
    if args.stylepath:
        spath = args.stylepath.split(os.pathsep)
    args.stylepath = spath

    if args.real_footnotes:
        args.inline_footnotes = True

    if args.invariant:
        patch_PDFDate()
        patch_digester()

    add_extensions(args)

    return RstToPdf(
        stylesheets=args.style,
        language=args.language,
        header=args.header, footer=args.footer,
        inlinelinks=args.inlinelinks,
        breaklevel=int(args.breaklevel),
        baseurl=args.baseurl,
        fit_mode=args.fit_mode,
        background_fit_mode=args.background_fit_mode,
        smarty=str(args.smarty),
        font_path=args.font_path,
        style_path=args.stylepath,
        repeat_table_rows=args.repeattablerows,
        footnote_backlinks=args.footnote_backlinks,
        inline_footnotes=args.inline_footnotes,
        real_footnotes=args.real_footnotes,
        default_dpi=int(args.default_dpi),
        basedir=args.basedir,
        show_frame=args.show_frame,
        splittables=args.splittables,
        blank_first_page=args.blank_first_page,
        first_page_on_right=args.first_page_on_right,
        breakside=args.breakside,
        custom_cover=args.custom_cover,
        floating_images=args.floating_images,
        numbered_links=args.numbered_links,
        raw_html=args.raw_html,
        section_header_depth=int(args.section_header_depth),
        strip_elements_with_classes=args.strip_elements_with_classes,
    ).createPdf(text=args.infile.read(),
                source_path=args.infile.name,
                output=args.outfile,
                compressed=args.compressed)


# Ugly hack that fixes Issue 335
import reportlab.lib.utils
reportlab.lib.utils.ImageReader.__deepcopy__ = lambda self, *x: copy.copy(self)


def patch_digester():
    """
    Patch digester so that we  get the same results when image filenames change
    """
    import reportlab.pdfgen.canvas as canvas

    cache = {}

    def _digester(s):
        index = cache.setdefault(s, len(cache))
        return 'rst2pdf_image_%s' % index
    canvas._digester = _digester


def patch_PDFDate():
    """
    Patch reportlab.pdfdoc.PDFDate so the invariant dates work correctly
    """
    from reportlab.pdfbase import pdfdoc
    import reportlab
    class PDFDate:
        __PDFObject__ = True
        # gmt offset now suppported
        def __init__(self, invariant=True, dateFormatter=None):
            now = (2000, 0o1, 0o1, 00, 00, 00, 0)
            self.date = now[:6]
            self.dateFormatter = dateFormatter

        def format(self, doc):
            from time import timezone
            dhh, dmm = timezone // 3600, (timezone % 3600) % 60
            dfmt = self.dateFormatter or (
                    lambda yyyy, mm, dd, hh, m, s:
                        "D:%04d%02d%02d%02d%02d%02d%+03d'%02d'" % (yyyy, mm, dd, hh, m, s, 0, 0))
            return pdfdoc.format(pdfdoc.PDFString(dfmt(*self.date)), doc)

    pdfdoc.PDFDate = PDFDate
    reportlab.rl_config.invariant = 1


def add_extensions(options):
    extensions = []
    for ext in options.extensions:
        if not ext.startswith('!'):
            extensions.append(ext)
            continue
        ext = ext[1:]
        try:
            extensions.remove(ext)
        except ValueError:
            log.warning('Could not remove extension %s -- no such extension installed' % ext)
        else:
            log.info('Removed extension %s' % ext)

    options.extensions[:] = extensions
    if not extensions:
        return

    class ModuleProxy(object):
        def __init__(self):
            self.__dict__ = globals()

    createpdf = ModuleProxy()
    for modname in options.extensions:
        prefix, modname = os.path.split(modname)
        path_given = prefix
        if modname.endswith('.py'):
            modname = modname[:-3]
            path_given = True
        if not prefix:
            prefix = os.path.join(os.path.dirname(__file__), 'extensions')
            if prefix not in sys.path:
                sys.path.append(prefix)
            prefix = os.getcwd()
        if prefix not in sys.path:
            sys.path.insert(0, prefix)
        log.info('Importing extension module %s', repr(modname))
        firstname = path_given and modname or (modname + '_r2p')
        try:
            try:
                module = importlib.import_module(firstname)
            except ImportError:
                module = importlib.import_module(modname)
        except ImportError:
            raise SystemExit('\nError: Could not find module %s '
                                'in sys.path [\n    %s\n]\nExiting...\n' %
                                (modname, ',\n    '.join(sys.path)))
        if hasattr(module, 'install'):
            module.install(createpdf, options)


def monkeypatch():
    """
    For initial test purposes, make reportlab 2.4 mostly perform like 2.3.
    This allows us to compare PDFs more easily.

    There are two sets of changes here:

    1)  rl_config.paraFontSizeHeightOffset = False

        This reverts a change reportlab that messes up a lot of docs.
        We may want to keep this one in here, or at least figure out
        the right thing to do.  If we do NOT keep this one here,
        we will have documents look different in RL2.3 than they do
        in RL2.4.  This is probably unacceptable.

    2) Everything else (below the paraFontSizeHeightOffset line):

        These change some behavior in reportlab that affects the
        graphics content stream without affecting the actual output.

        We can remove these changes after making sure we are happy
        and the checksums are good.
    """
    import reportlab
    from reportlab import rl_config
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfbase import pdfdoc

    if getattr(reportlab, 'Version', None) != '2.4':
        return

    # NOTE:  THIS IS A REAL DIFFERENCE -- DEFAULT y-offset FOR CHARS CHANGES!!!
    rl_config.paraFontSizeHeightOffset = False

    # Fix the preamble.  2.4 winds up injecting an extra space, so we toast it.

    def new_make_preamble(self):
        self._old_make_preamble()
        self._preamble = ' '.join(self._preamble.split())

    Canvas._old_make_preamble = Canvas._make_preamble
    Canvas._make_preamble = new_make_preamble

    # A new optimization removes the CR/LF between 'endstream' and 'endobj'
    # Remove it for comparison
    pdfdoc.INDIRECTOBFMT = pdfdoc.INDIRECTOBFMT.replace('CLINEEND', 'LINEEND')

    # By default, transparency is set, and by default, that changes PDF version
    # to 1.4 in RL 2.4.
    pdfdoc.PDF_SUPPORT_VERSION['transparency'] = 1, 3


monkeypatch()


def publish_secondary_doctree(text, main_tree, source_path):
    # This is a hack so the text substitutions defined
    # in the document are available when we process the cover
    # page. See Issue 322
    dt = main_tree
    # Add substitutions  from the main doctree
    class addSubsts(Transform):
        default_priority = 219

        def apply(self):
            self.document.substitution_defs.update(dt.substitution_defs)
            self.document.substitution_names.update(dt.substitution_names)

    # Use an own reader to modify transformations done.
    class Reader(standalone.Reader):

        def get_transforms(self):
            default = standalone.Reader.get_transforms(self)
            return (default + [ addSubsts, ])

    # End of Issue 322 hack

    return docutils.core.publish_doctree(text,
        reader=Reader(), source_path=source_path)


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
