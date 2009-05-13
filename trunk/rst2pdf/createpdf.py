# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$
__docformat__ = 'reStructuredText'

import re
import sys
import os
from os.path import join, abspath, dirname
import pprint
import string
from types import StringType
from urlparse import *
from copy import copy
from cgi import escape
import logging
from optparse import OptionParser
from docutils import __version__, __version_details__, SettingsSpec
from docutils import frontend, io, utils, readers, writers
from docutils.languages import get_language
from docutils.transforms import Transformer
import docutils.readers.doctree
import docutils.core
import docutils.nodes

import pygments_code_block_directive

import reportlab
from reportlab.platypus import *
from reportlab.platypus.flowables import _listWrapOn,_Container
from reportlab.pdfbase.pdfmetrics import stringWidth
import reportlab.lib.colors as colors
from reportlab.lib.enums import *
from reportlab.lib.units import *
from reportlab.lib.pagesizes import *

from flowables import *
from svgimage import SVGImage
from math_directive import math_node
from math_flowable import Math
from log import log
from smartypants import smartyPants

import config

#def escape (x,y):
#    "Dummy escape function to test for excessive escaping"
#    return x
from utils import log,parseRaw
import styles as sty

try:
    from PIL import Image as PILImage
except ImportError:
    try:
        import Image as PILImage
    except ImportError:
        log.warning("No support for images other than JPG, and limited support for image size. Please install PIL")

haveWordaxe=False
try:
    import wordaxe
    from wordaxe.rl.paragraph import Paragraph
    from wordaxe.rl.styles import ParagraphStyle, getSampleStyleSheet
    from wordaxe.DCWHyphenator import DCWHyphenator
    from wordaxe.PyHnjHyphenator import PyHnjHyphenator
    haveWordaxe=True
    from wordaxe.plugins.PyHyphenHyphenator import PyHyphenHyphenator
except ImportError:
    #log.warning("No support for hyphenation, install wordaxe")
    pass

try:
    import sphinx
    HAS_SPHINX=True
except ImportError:
    HAS_SPHINX=False

class RstToPdf(object):

    def __init__(self, stylesheets = [], language = 'en_US', header=None, footer=None,
                 inlinelinks=False, breaklevel=1, fontPath=[], stylePath=[],
                 fitMode='shrink' ,sphinx=False, smarty='0', baseurl=None, repeatTableRows=False):
        global HAS_SPHINX
        self.language=language
        self.lowerroman=['i','ii','iii','iv','v','vi','vii','viii','ix','x','xi']
        self.loweralpha=string.ascii_lowercase
        self.doc_title=""
        self.doc_author=""
        self.decoration = {'header':header, 'footer':footer, 'endnotes':[]}
        stylesheets = [os.path.join(abspath(dirname(__file__)),'styles','styles.json')]+stylesheets
        self.styles=sty.StyleSheet(stylesheets,fontPath,stylePath)
        self.docutils_languages={}
        self.inlinelinks=inlinelinks
        self.breaklevel=breaklevel
        self.fitMode=fitMode
        self.to_unlink=[]
        self.smarty=smarty
        self.baseurl=baseurl
        self.repeatTableRows=repeatTableRows
        # Sorry about this, but importing sphinx.roles makes some
        # ordinary documents fail (demo.txt specifically) so
        # I can' t just try to import it outside. I need
        # to do it only if it's requested
        if HAS_SPHINX and sphinx:
            import sphinx.roles
        else:
            HAS_SPHINX=False

        if not self.styles.languages:
            self.styles.languages=[language]
            self.styles['bodytext'].language=language

        # Load the docutils language modules for all required languages
        for lang in self.styles.languages:
            try:
                self.docutils_languages[lang] = get_language(lang)
            except ImportError:
                try:
                    self.docutils_languages[lang] = get_language(lang.split('_',1)[0])
                except ImportError:
                    log.warning("Can't load Docutils module for language %s",lang)

        # Load the hyphenators for all required languages
        if haveWordaxe:
            for lang in self.styles.languages:
                if lang.split('_', 1)[0] == 'de':
                    wordaxe.hyphRegistry[lang] = DCWHyphenator('de',5)
                else:
                    try:
                        wordaxe.hyphRegistry[lang] = PyHyphenHyphenator(lang)
                    except Exception:
                        log.warning("Can't load PyHyphen hyphenator for language %s, trying PyHnj hyphenator",lang)
                        wordaxe.hyphRegistry[lang] = PyHnjHyphenator(lang,5,purePython=True)
            log.info('hyphenation by default in %s , loaded %s',
                self.styles['bodytext'].language, ','.join(self.styles.languages))

    def style_language(self, style):
        """Return language corresponding to this style."""
        try:
            return style.language
        except AttributeError:
            return self.styles['bodytext'].language

    def text_for_label(self, label, style):
        """Translate text for label."""
        try:
            text = self.docutils_languages[self.style_language(style)].labels[label]
        except KeyError:
            text = label.capitalize()
        return text + ":"

    def text_for_bib_field(self, field, style):
        """Translate text for bibliographic fields."""
        try:
            text = self.docutils_languages[self.style_language(style)].bibliographic_fields[field]
        except KeyError:
            text = field
        return text + ":"

    def author_separator(self, style):
        """Return separator string for authors."""
        try:
            sep = self.docutils_languages[self.style_language(style)].author_separators[0]
        except KeyError:
            sep = ';'
        return sep + " "

    def styleToFont(self, style):
        '''Takes a style name, returns a font tag for it, like
        "<font face=helvetica size=14 color=red>". Used for inline
        nodes (custom interpreted roles)'''

        try:
            s=self.styles[style]
            bc=s.backColor
            if bc:
                r='<font face="%s" size="%d" color="#%s" backColor="#%s">' % (s.fontName,s.fontSize,
                                                                              s.textColor.hexval()[2:],
                                                                              bc.hexval()[2:])
            else:
                r='<font face="%s" size="%d" color="#%s">' % (s.fontName,s.fontSize,s.textColor.hexval()[2:])
            return r
        except KeyError:
            log.warning('Unknown class %s', style)
            return None


    def gather_pdftext (self, node, depth,replaceEnt=True):
        return ''.join([self.gen_pdftext(n,depth,replaceEnt) for n in node.children ])

    def gen_pdftext(self, node, depth, replaceEnt=True):
        pre=""
        post=""

        log.debug("self.gen_pdftext: %s", node.__class__)
        try:
            log.debug("self.gen_pdftext: %s", node)
        except (UnicodeDecodeError, UnicodeEncodeError):
            log.debug("self.gen_pdftext: %r", node)

        if isinstance (node, docutils.nodes.paragraph) \
            or isinstance (node, docutils.nodes.title) \
            or isinstance (node, docutils.nodes.subtitle):
            node.pdftext=self.gather_pdftext(node,depth)+"\n"

        elif isinstance (node, docutils.nodes.Text):
            node.pdftext=node.astext()
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.strong):
            pre="<b>"
            post="</b>"
            node.pdftext=self.gather_pdftext(node,depth)
            #if replaceEnt:
            #    node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.emphasis):
            pre="<i>"
            post="</i>"
            node.pdftext=self.gather_pdftext(node,depth)
            #if replaceEnt:
            #    node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.literal):
            pre='<font face="%s">'%self.styles['literal'].fontName
            post="</font>"
            if not self.styles['literal'].hyphenation:
                pre = '<nobr>'+pre
                post += '</nobr>'
            node.pdftext=self.gather_pdftext(node,depth)
            #if replaceEnt:
            #    node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.superscript):
            pre='<super>'
            post="</super>"
            node.pdftext=self.gather_pdftext(node,depth)
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.subscript):
            pre='<sub>'
            post="</sub>"
            node.pdftext=self.gather_pdftext(node,depth)
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.title_reference):
            pre=self.styleToFont("title_reference")
            post="</font>"
            node.pdftext=self.gather_pdftext(node,depth)
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.reference) :
            uri=node.get('refuri')
            if uri:
                if self.baseurl: # Need to join the uri with the base url
                    uri=urljoin(self.baseurl,uri)
                if urlparse(uri)[0]:
                    if self.inlinelinks:
                        #import pdb; pdb.set_trace()
                        post = u' (%s)' % uri
                    else:
                        pre+=u'<a href="%s" color="%s">'%(uri,self.styles.linkColor)
                        post='</a>'+post
            else:
                uri=node.get('refid')
                if uri:
                    pre+=u'<a href="#%s" color="%s">'%(uri,self.styles.linkColor)
                    post='</a>'+post
            node.pdftext=self.gather_pdftext(node,depth)
            #if replaceEnt:
            #    node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.option_string) \
            or isinstance (node, docutils.nodes.option_argument):
            node.pdftext=node.astext()
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)

        elif isinstance (node, docutils.nodes.header) \
            or isinstance (node, docutils.nodes.footer):
            node.pdftext=self.gather_pdftext(node,depth)
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)

            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.system_message)     \
            or isinstance (node, docutils.nodes.problematic):
            pre='<font color="red">'
            post="</font>"
            node.pdftext=self.gather_pdftext(node,depth)
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.generated):
            node.pdftext=self.gather_pdftext(node,depth)
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext+post

        elif isinstance (node, docutils.nodes.image):
            node.pdftext='<img src="%s" />'%node.get('uri')

        elif isinstance (node, math_node):
            # FIXME: implement this using inline images
            mf=Math(node.math_data)
            w,h=mf.wrap(0,0)
            descent=mf.descent()
            img=mf.genImage()
            self.to_unlink.append(img)
            node.pdftext='<img src="%s" width=%f height=%f valign=%f/>'%(img,w,h,-descent)

        elif isinstance (node, docutils.nodes.footnote_reference):
            # Fixme link to the right place
            anchors=''.join(['<a name="%s"/>'%i for i in node['ids'] ])
            node.pdftext=u'%s<super><a href="%s" color="%s">%s</a></super>'%(
                anchors,'#'+node.astext(),self.styles.linkColor,node.astext())
        elif isinstance (node, docutils.nodes.citation_reference):
            # Fixme link to the right place
            anchors=''.join(['<a name="%s"/>'%i for i in node['ids'] ])
            node.pdftext=u'%s[<a href="%s" color="%s">%s</a>]'%(
                anchors,'#'+node.astext(),self.styles.linkColor,node.astext())

        elif isinstance (node, docutils.nodes.target):
            pre=u'<a name="%s"/>'%node['ids'][0]
            node.pdftext=self.gather_pdftext(node,depth)
            if replaceEnt:
                node.pdftext=escape(node.pdftext,True)
            node.pdftext=pre+node.pdftext

        elif isinstance (node, docutils.nodes.inline):
            ftag=self.styleToFont(node['classes'][0])
            if ftag:
                node.pdftext="%s%s</font>"%(ftag,self.gather_pdftext(node,depth))
            else:
                node.pdftext=self.gather_pdftext(node,depth)

        else:
            log.warning("Unkn. node (self.gen_pdftext): %s", node.__class__)
            try:
                log.debug(node)
            except (UnicodeDecodeError, UnicodeEncodeError):
                log.debug(repr(node))
            node.pdftext=self.gather_pdftext(node,depth)

        try:
            log.debug("self.gen_pdftext: %s" % node.pdftext)
        except UnicodeDecodeError:
            pass
        # Try to be clever about when to use smartypants
        if node.__class__ in [docutils.nodes.paragraph,
                              docutils.nodes.block_quote,
                              docutils.nodes.title
                              ]:
            node.pdftext=smartyPants(node.pdftext,self.smarty)

        return node.pdftext

    def gen_elements(self, node, depth, style=None):

        log.debug("gen_elements: %s", node.__class__)
        try:
            log.debug("gen_elements: %s", node)
        except (UnicodeDecodeError, UnicodeEncodeError):
            log.debug("gen_elements: %r", node)

        if style is None:
            style=self.styles.styleForNode(node)

        try:
            if node['classes']:
                # Supports only one class, sorry ;-)
                try:
                    style=self.styles[node['classes'][0]]
                except:
                    log.info("Unknown class %s, using class bodytext.", node['classes'][0])
        except TypeError: # Happens when a docutils.node.Text reaches here
            pass

        if isinstance (node, docutils.nodes.document):
            node.elements=self.gather_elements(node,depth,style=style)

        elif HAS_SPHINX and isinstance(node,sphinx.addnodes.glossary):
            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node,math_node):
            node.elements=[Math(node.math_data)]

        #######################
        ## Tables
        #######################

        elif isinstance (node, docutils.nodes.table):
            # FIXME: make spacing configurable
            node.elements=[Spacer(0,6)]+self.gather_elements(node,depth)

        elif isinstance (node, docutils.nodes.tgroup):
            rows=[]
            colwidths=[]
            hasHead=False
            headRows=0
            for n in node.children:
                if isinstance (n,docutils.nodes.thead):
                    hasHead=True
                    for row in n.children:
                        r=[]
                        for cell in row.children:
                            r.append(cell)
                        rows.append(r)
                    headRows=len(rows)
                elif isinstance (n,docutils.nodes.tbody):
                    for row in n.children:
                        r=[]
                        for cell in row.children:
                            r.append(cell)
                        rows.append(r)
                elif isinstance (n,docutils.nodes.colspec):
                    colwidths.append(int(n['colwidth']))

            spans=self.filltable (rows)

            data=[]
            cellStyles=[]
            rowids=range(0,len(rows))
            for row,i in zip(rows,rowids):
                r=[]
                j=0
                for cell in row:
                    if isinstance(cell,str):
                        r.append("")
                    else:
                        if i<headRows:
                            ell=self.gather_elements(cell,depth,style=self.styles['table-heading'])
                        else:
                            ell=self.gather_elements(cell,depth,style=style)
                        if len(ell)==1:
                            # Experiment: if the cell has a single element, extract its
                            # class and use it for the cell. That way, you can have cells
                            # with specific background colors, at least

                            try:
                                cellStyles+=self.styles.pStyleToTStyle(ell[0].style,j,i)
                            except AttributeError: # Fix for issue 85: only do it if it has a style.
                                pass
                        r.append(ell)
                    j+=1
                data.append(r)

            st=spans+sty.tstyleNorm+self.styles.tstyleBody()+cellStyles

            if hasHead:
                st+=self.styles.tstyleHead(headRows)

            rtr = self.repeatTableRows

            #node.elements=[Table(data,colWidths=colwidths,style=TableStyle(st))]
            node.elements=[DelayedTable(data,colwidths,st,rtr)]

        elif isinstance (node, docutils.nodes.title):
            # Special cases: (Not sure this is right ;-)
            if isinstance (node.parent, docutils.nodes.document):
                # FIXME maybe make it a coverpage?
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['title'])]
                self.doc_title=unicode(self.gen_pdftext(node,depth)).strip()
            elif isinstance (node.parent, docutils.nodes.topic):
                # FIXME style correctly
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['heading3'])]
            elif isinstance (node.parent, docutils.nodes.admonition):
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['heading3'])]
            elif isinstance (node.parent, docutils.nodes.table):
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['table-title'])]
            elif isinstance (node.parent, docutils.nodes.sidebar):
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['sidebar-title'])]
            else:
                # Section/Subsection/etc.
                text=self.gen_pdftext(node,depth)
                fch=node.children[0]
                if isinstance(fch,docutils.nodes.generated) and fch['classes']==['sectnum']:
                    snum=fch.astext()
                else:
                    snum=None
                key=node.get('refid')
                elem = OutlineEntry(key,text,depth-1,snum)
                elem.parent_id = node.parent.get('ids', [None])[0]
                node.elements=[KeepTogether([elem, Paragraph(text, self.styles['heading%d' % min(depth,3)])])]
                if depth <=self.breaklevel:
                    node.elements.insert(0,MyPageBreak())


        elif isinstance (node, docutils.nodes.subtitle):
            if isinstance (node.parent,docutils.nodes.sidebar):
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['sidebar-subtitle'])]
            elif isinstance (node.parent,docutils.nodes.document):
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['subtitle'])]

        elif HAS_SPHINX and isinstance(node,sphinx.addnodes.compact_paragraph):
            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.paragraph):
            node.elements=[Paragraph(self.gen_pdftext(node,depth), style)]

        elif isinstance (node, docutils.nodes.docinfo):
            # A docinfo usually contains several fields.
            # We'll render it as a series of elements, one field each.

            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.field):
            # A field has two child elements, a field_name and a field_body.
            # We render as a two-column table, left-column is right-aligned,
            # bold, and much smaller

            fn=Paragraph(self.gather_pdftext(node.children[0],depth)+":",style=self.styles['fieldname'])
            fb=self.gen_elements(node.children[1],depth)
            node.elements=[Table([[fn,fb]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])]

        elif isinstance (node, docutils.nodes.decoration):
            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.header):
            self.decoration['header']=self.gather_elements(node,depth,style=self.styles['header'])
            node.elements=[]
        elif isinstance (node, docutils.nodes.footer):
            self.decoration['footer']=self.gather_elements(node,depth,style=self.styles['footer'])
            node.elements=[]

        elif isinstance (node, docutils.nodes.author):
            if isinstance (node.parent,docutils.nodes.authors):
                # Is only one of multiple authors. Return a paragraph
                node.elements=[Paragraph(self.gather_pdftext(node,depth), style=style)]
                if self.doc_author:
                    self.doc_author+=self.author_separator(style=style)+node.astext().strip()
                else:
                    self.doc_author=node.astext().strip()
            else:
                # A single author: works like a field
                fb=self.gather_pdftext(node,depth)
                node.elements=[Table([[Paragraph(self.text_for_label("author",style) ,style=self.styles['fieldname']),
                                    Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])]
                self.doc_author=node.astext().strip()

        elif isinstance (node, docutils.nodes.authors):
            # Multiple authors. Create a two-column table. Author references on the right.
            td=[[Paragraph(self.text_for_label("authors",style),style=self.styles['fieldname']),
                self.gather_elements(node,depth,style=style)]]
            node.elements=[Table(td,style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])]

        elif isinstance (node, docutils.nodes.organization):
            fb=self.gather_pdftext(node,depth)
            t=Table([[Paragraph(self.text_for_label("organization",style),style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.contact):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph(self.text_for_label("contact",style),style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.address):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph(self.text_for_label("address",style),style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.version):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph(self.text_for_label("version",style),style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.revision):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph(self.text_for_label("revision",style),style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.status):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph(self.text_for_label("status",style),style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.date):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph(self.text_for_label("date",style),style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.copyright):
            fb=self.gather_pdftext(node,depth)
            t=Table([[Paragraph(self.text_for_label("copyright",style),style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]

        elif isinstance (node, docutils.nodes.topic):
            # toc
            node_classes = node.attributes.get('classes', [])
            if 'contents' in node_classes:
                toc_visitor = TocBuilderVisitor(node.document)
                toc_visitor.toc = MyTableOfContents()
                toc_visitor.toc.linkColor = self.styles.linkColor
                node.walk(toc_visitor)
                toc = toc_visitor.toc
                # Override fontnames (defaults to Times-Roman)
                for levelStyle in toc.levelStyles:
                    levelStyle.__dict__['fontName'] = self.styles['tableofcontents'].fontName
                if 'local' in node_classes:
                    node.elements = [toc]
                else:
                    node.elements = [Paragraph(self.gen_pdftext(node.children[0],depth), self.styles['title']), toc]
            else:
                node.elements = self.gather_elements(node, depth, style=style)

        elif isinstance (node, docutils.nodes.field_body):
            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.section):
            node.elements=self.gather_elements(node,depth+1)

        elif isinstance (node, docutils.nodes.bullet_list):
            node.elements=self.gather_elements(node,depth,style=self.styles["bullet_list_item"])
            s = self.styles["bullet_list"]
            if s.spaceBefore:
                node.elements.insert(0, Spacer(0,s.spaceBefore))
            if s.spaceAfter:
                node.elements.append(Spacer(0,s.spaceAfter))

        elif isinstance (node, docutils.nodes.definition_list)\
            or isinstance (node, docutils.nodes.option_list)  \
            or isinstance (node, docutils.nodes.field_list):

            node.elements=self.gather_elements(node,depth,style=style)


        elif isinstance (node, docutils.nodes.enumerated_list):
            node.elements=self.gather_elements(node,depth,style=self.styles["enumerated_list_item"])
            s = self.styles["enumerated_list"]
            if s.spaceBefore:
                node.elements.insert(0, Spacer(0,s.spaceBefore))
            if s.spaceAfter:
                node.elements.append(Spacer(0,s.spaceAfter))

        elif isinstance (node, docutils.nodes.definition):
            node.elements=self.gather_elements(node,depth,style=self.styles["definition"])

        elif isinstance (node, docutils.nodes.option_list_item):

            optext = ', '.join([self.gather_pdftext(child,depth) for child in node.children[0].children])
            desc = self.gather_elements(node.children[1],depth,style)

            node.elements=[Table([[self.PreformattedFit(optext,self.styles["literal"]),desc]],style=sty.tstyles['field'])]


        elif isinstance (node, docutils.nodes.definition_list_item):

            # I need to catch the classifiers here
            tt=[]
            dt=[]
            for n in node.children:
                if isinstance(n,docutils.nodes.term):
                    for i in n['ids']: # Used by sphinx glossary lists
                        tt.append('<a name="%s"/>'%i)
                    tt.append(self.styleToFont("definition_list_term")+self.gather_pdftext(n,depth,style)+"</font>")
                elif isinstance(n,docutils.nodes.classifier) :
                    tt.append(self.styleToFont("definition_list_classifier")+self.gather_pdftext(n,depth,style)+"</font>")
                else:
                    dt=dt+self.gen_elements(n,depth,style)

            node.elements=[Paragraph(' : '.join(tt),self.styles['definition_list_term']),
                           MyIndenter(left=10)]+dt+[MyIndenter(left=-10)]

        elif isinstance (node, docutils.nodes.list_item):

            el=self.gather_elements(node,depth,style=style)
            b=""
            if node.parent.get('start'):
                start=int(node.parent.get('start'))
            else:
                start=1

            if node.parent.get('bullet') or isinstance(node.parent,docutils.nodes.bullet_list):
                b=node.parent.get('bullet')
                if b=="None":
                    b=""

            elif node.parent.get ('enumtype')=='arabic':
                b=str(node.parent.children.index(node)+start)+'.'

            elif node.parent.get ('enumtype')=='lowerroman':
                b=str(self.lowerroman[node.parent.children.index(node)+start-1])+'.'
            elif node.parent.get ('enumtype')=='upperroman':
                b=str(self.lowerroman[node.parent.children.index(node)+start-1].upper())+'.'
            elif node.parent.get ('enumtype')=='loweralpha':
                b=str(self.loweralpha[node.parent.children.index(node)+start-1])+'.'
            elif node.parent.get ('enumtype')=='upperalpha':
                b=str(self.loweralpha[node.parent.children.index(node)+start-1].upper())+'.'
            else:
                log.critical("Unknown kind of list_item %s", node.parent)
                sys.exit(1)

            # FIXME: this is really really not good code
            if not el:
                el=[Paragraph(u"\xa0",self.styles["bodytext"])]

            # FIXME: use different unicode bullets depending on b
            if b and b in "*+-":
                b=u'\u2022'
            el[0].bulletText = b
            
            # Try to figure out how much space to reserve for the bullet
            if "style" in el[0].__dict__:
                indentation=el[0].style.leading
            else:
                indentation=12


            # Indent all elements inside the list
            for e in el:
                if "style" in e.__dict__:
                    if isinstance(e.style,list): # Table style
                        # Add pre/post indenters. Later these sublists are flattened in node.elements
                        el[el.index(e)]=[MyIndenter(left=2*indentation),e,MyIndenter(left=-2*indentation)]
                    else: # Paragraph style
                        indentedStyle=copy(e.style)
                        indentedStyle.leftIndent+=indentation
                        indentedStyle.bulletIndent+=indentation
                        e.style=indentedStyle
            for e in el:
                if not isinstance(e,list) and 'style' in e.__dict__:
                    e.style.leftIndent=e.style.bulletIndent+indentation

            # "Flatten" el
            node.elements=[]
            for e in el:
                if isinstance(e,list):
                    node.elements+=e
                else:
                    node.elements.append(e)
            #node.elements=el

        elif isinstance (node, docutils.nodes.transition):
            node.elements=[Separation()]


        elif isinstance (node, docutils.nodes.system_message)     \
            or isinstance (node, docutils.nodes.problematic):
            # FIXME show the error in the document, red, whatever
            #log.warning("Problematic node %s", node.astext())
            node.elements=[]

        elif isinstance (node, docutils.nodes.block_quote):
            node.elements=[MyIndenter(left=20)]+self.gather_elements(node,depth,style)+[MyIndenter(left=-20)]

        elif isinstance (node, docutils.nodes.attribution):
            node.elements=[Paragraph(self.gather_pdftext(node,depth),self.styles['attribution'])]

        elif isinstance (node, docutils.nodes.comment):
            # Class that generates no output
            node.elements=[]

        elif isinstance (node, docutils.nodes.line_block):
            # Obsolete? Let's do something anyway.
            # FIXME: indent or not?
            qstyle=copy(style)
            qstyle.leftIndent+=30
            node.elements=self.gather_elements(node,depth,style=qstyle)

        elif isinstance (node, docutils.nodes.line):
            # All elements in one line
            node.elements=[Paragraph(self.gather_pdftext(node,depth),style=style)]

        elif isinstance (node, docutils.nodes.literal_block) \
            or isinstance (node, docutils.nodes.doctest_block):
            node.elements=[self.PreformattedFit(self.gather_pdftext(node,depth,replaceEnt=True),self.styles['code'])]

        elif isinstance (node, docutils.nodes.attention)        \
            or isinstance (node, docutils.nodes.caution)        \
            or isinstance (node, docutils.nodes.danger)         \
            or isinstance (node, docutils.nodes.error)          \
            or isinstance (node, docutils.nodes.hint)           \
            or isinstance (node, docutils.nodes.important)      \
            or isinstance (node, docutils.nodes.note)           \
            or isinstance (node, docutils.nodes.tip)            \
            or isinstance (node, docutils.nodes.warning)        \
            or isinstance (node, docutils.nodes.admonition):
            #node.elements=[Paragraph(node.tagname.title(),style=self.styles['heading3'])]+self.gather_elements(node,depth,style=style)
                rows=[Paragraph(node.tagname.title(),style=self.styles['heading3'])]+self.gather_elements(node,depth,style=style)
                node.elements=[BoxedContainer(rows,self.styles['admonition'])]

        elif isinstance (node, docutils.nodes.image):
            # FIXME: handle all the other attributes

            imgname=str(node.get("uri"))

            # Figuring out the size to display of an image is ... annoying.
            # If the user provides a size with a unit, it's simple, adjustUnits
            # will return it in points and we're done.

            # However, often the unit wil be "%" (specially if it's meant for
            # HTML originally.In which case, we will use the following:

            # Find the image size in pixels:

            try:
                # FIXME find extensions uniconvertor supports
                if imgname.split('.')[-1].lower() in ["ai","ccx","cdr","cgm","cmx","sk1","sk","svg","xml","wmf","fig"]:
                    iw,ih=SVGImage(imgname).wrap(0,0)
                else:
                    img=PILImage.open(imgname)
                    iw,ih=img.size
                # Assume a DPI of 300, which is pretty much made up,
                # and then a 100% size would be iw*inch/300, so we pass
                # that as the second parameter to adjustUnits

                w=node.get('width')
                if w is not None:
                    if iw:
                        w=self.styles.adjustUnits(w,iw*inch/300)
                    else:
                        w=self.styles.adjustUnits(w,self.styles.pw*.5)
                else:
                    log.warning("Using image %s without specifying size."
                        "Calculating based on 300dpi", imgname)
                    # No width specified at all. Make it up
                    # as if we knew what we're doing
                    if iw:
                        w=iw*inch/300
                    else:
                        w=2*inch # We are getting desperate here ;-)

                h=node.get('height')
                if h is not None:
                    if ih:
                        h=self.styles.adjustUnits(h,ih*inch/300)
                    else:
                        h=self.styles.adjustUnits(h,self.styles.ph*.5)
                else:
                    # Now, often, only the width is specified!
                    # if we don't have a height, we need to keep the
                    # aspect ratio, or else it will look ugly
                    if iw:
                        h=w*ih/iw
                    else:
                        h=2*inch # We are getting desperate here ;-)

                # And now we have this probably completely bogus size!
                log.info("Image %s size calculated:  %fcm by %fcm",
                    imgname, w/cm, h/cm)
                if imgname.split('.')[-1].lower() in ["ai","ccx","cdr","cgm","cmx","sk1","sk","svg","xml","wmf","fig"]:
                    node.elements=[SVGImage(filename=imgname,
                                            height=h,
                                            width=w)]
                else:
                    node.elements=[Image(filename=imgname,
                                         height=h,
                                         width=w)]
                i=node.elements[0]
                if node.get('align'):
                    i.hAlign=node.get('align').upper()
                else:
                    i.hAlign='CENTER'
            except IOError,e: #No image, or no permissions
                log.error('Error opening "%s": %s'%(imgname,str(e)))
                node.elements=[]


        elif isinstance (node, docutils.nodes.figure):
            # The sub-elements are the figure and the caption, and't ugly if
            # they separate
            #node.elements=[KeepTogether(self.gather_elements(node,depth,style=self.styles["figure"]))]
            # FIXME: using KeepTogether as a container fails inside a float.
            node.elements=self.gather_elements(node,depth,style=self.styles["figure"])

        elif isinstance (node, docutils.nodes.caption):
            node.elements=[Paragraph('<i>'+self.gather_pdftext(node,depth)+'</i>',style=style)]

        elif isinstance (node, docutils.nodes.legend):
            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.sidebar):
            node.elements=[BoxedContainer(self.gather_elements(node,depth,style=None),self.styles['sidebar'])]

        elif isinstance (node, docutils.nodes.rubric):
            node.elements=[Paragraph(self.gather_pdftext(node,depth),self.styles['rubric'])]

        elif isinstance (node, docutils.nodes.compound):
            # FIXME think if this is even implementable
            node.elements=self.gather_elements(node,depth,style)

        elif isinstance (node, docutils.nodes.container):
            # FIXME think if this is even implementable
            node.elements=self.gather_elements(node,depth,style)

        elif isinstance (node, docutils.nodes.substitution_definition):
            node.elements=[]

        elif isinstance (node, docutils.nodes.tbody):
            rows=[self.gen_elements(n,depth) for n in node.children]
            t=[]
            for r in rows:
                if not r:
                    continue
                t.append(r)
            node.elements=[Table(t,style=sty.tstyles['normal'])]

        elif isinstance (node, docutils.nodes.footnote) or \
            isinstance (node, docutils.nodes.citation):
            # It seems a footnote contains a label and a series of elements
            ltext=self.gather_pdftext(node.children[0],depth)
            if len(node['backrefs'])>1:
                backrefs=[]
                i=1
                for r in node['backrefs']:
                    backrefs.append('<a href="#%s" color="%s">%d</a>'%(
                        r,self.styles.linkColor,i))
                    i+=1
                backrefs='(%s)'%', '.join(backrefs)
                label=Paragraph('<a name="%s"/>%s'%(ltext,ltext+backrefs),self.styles["normal"])
            elif len(node['backrefs'])==1:
                label=Paragraph('<a name="%s"/><a href="%s" color="%s">%s</a>'%(
                    ltext,node['backrefs'][0],self.styles.linkColor,ltext),self.styles["normal"])
            else:
                label=Paragraph('<a name="%s"/>%s'%(ltext,ltext),self.styles["normal"])
            contents=self.gather_elements(node,depth,style)[1:]
            self.decoration['endnotes'].append([label,contents])
            node.elements=[]

        elif isinstance (node, docutils.nodes.label):
            node.elements=[Paragraph(self.gather_pdftext(node,depth),style)]
        elif isinstance (node, docutils.nodes.Text):
            node.elements=[Paragraph(self.gather_pdftext(node,depth),style)]
        elif isinstance (node, docutils.nodes.entry):
            node.elements=self.gather_elements(node,depth,style)

        elif isinstance (node, docutils.nodes.target):
            node.elements=self.gather_elements(node,depth,style)

        elif isinstance (node, docutils.nodes.reference):
            node.elements=self.gather_elements(node,depth,style)

        elif isinstance (node, docutils.nodes.raw):
            # Not really raw, but what the heck
            node.elements=parseRaw(str(node.astext()))

        # FIXME nodes we are ignoring for the moment
        elif isinstance (node, docutils.nodes.citation):
            node.elements=[]
        else:
            log.error("Unkn. node (gen_elements): %s", str(node.__class__))
            # Why fail? Just log it and do our best.
            try:
                log.debug(node)
            except (UnicodeDecodeError, UnicodeEncodeError):
                log.debug(repr(node))
            node.elements=self.gather_elements(node,depth,style)
            #sys.exit(1)

        # set anchors for internal references
        try:
            for i in node['ids']:
                # ids should link **after** pagebreaks
                if len(node.elements) and isinstance(node.elements[0],MyPageBreak):
                    idx=1
                else:
                    idx=0
                node.elements.insert(idx,Reference(i))
        except TypeError: #Hapens with docutils.node.Text
            pass

        # Make all the sidebar cruft unreachable
        #if style.__dict__.get('float','None').lower()<>'none':
            #node.elements=[Sidebar(node.elements,style)]
        #elif 'width' in style.__dict__:
        if 'width' in style.__dict__:
            node.elements=[BoundByWidth(style.width,node.elements,style,mode="shrink")]
        try:
            log.debug("gen_elements: %s", node.elements)
        except: # unicode problems FIXME: explicit error
            pass
        return node.elements

    def gather_elements (self,node, depth,style=None):
        if style is None:
            style=self.styles.styleForNode(node)
        r=[]
        if 'float' in style.__dict__: style = None # Don't pass floating styles to children!
        for n in node.children:
            #import pdb; pdb.set_trace()
            r.extend(self.gen_elements(n,depth,style=style))
        return r

    def filltable (self,rows):
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

        for y in range(0,len(rows)):
            for x in range (0,len(rows[y])):
                cell=rows[y][x]
                if isinstance (cell,str):
                    continue
                if cell.get("morecols"):
                    for i in range(0,cell.get("morecols")):
                        rows[y].insert(x+1,"")

        for y in range(0,len(rows)):
            for x in range (0,len(rows[y])):
                cell=rows[y][x]
                if isinstance (cell,str):
                    continue
                if cell.get("morerows"):
                    for i in range(0,cell.get("morerows")):
                        rows[y+i+1].insert(x,"")


        # If a row is shorter, add empty cells at the right end
        maxw=max([len(r) for r in rows])
        for r in rows:
            while len(r) < maxw:
                r.append("")

        # Create spans list for reportlab's table style
        spans=[]
        for y in range(0,len(rows)):
            for x in range (0,len(rows[y])):
                cell=rows[y][x]
                if isinstance (cell,str):
                    continue
                if cell.get("morecols"):
                    mc=cell.get("morecols")
                else: mc=0
                if cell.get("morerows"):
                    mr=cell.get("morerows")
                else: mr=0

                if mc or mr:
                    spans.append(('SPAN',(x,y),(x+mc,y+mr)))
        return spans

    def PreformattedFit(self,text,style):
        """Preformatted section that gets horizontally compressed if needed."""
        # Pass a ridiculous size, then it will shrink to what's available
        # in the frame
        return BoundByWidth(2000*cm,content=[XPreformatted(text,style)],mode=self.fitMode,style=style)

    def createPdf(self,text=None,source_path=None,output=None,doctree=None,
                  compressed=False):
        '''Create a PDF from text (ReST input), or doctree (docutil nodes)
        and save it in outfile.

        If outfile is a string, it's a filename.
        If it's something with a write method, (like a StringIO,
        or a file object), the data is saved there.

        '''

        if doctree is None:
            if text is not None:
                doctree=docutils.core.publish_doctree(text,source_path=source_path,
                             settings_overrides={'language_code':self.language})
                log.debug(doctree)
            else:
                log.error('Error: createPdf needs a text or a doctree to be useful')
                return
        elements=self.gen_elements(doctree,0)

        # Put the endnotes at the end ;-)
        endnotes = self.decoration['endnotes']
        if endnotes:
            elements.append(Spacer(1,2*cm))
            elements.append(Separation())
            # FIXME: the width of the left column should not be fixed
            for n in self.decoration['endnotes']:
                elements.append(Table([[n[0],n[1]]],
                                style=sty.tstyles['endnote'],
                                colWidths=[sty.endnote_lwidth,None]))

        head=self.decoration['header']
        foot=self.decoration['footer']

        # So, now, create the FancyPage with the right sizes and elements
        FP=FancyPage("fancypage",head,foot,self.styles,smarty=self.smarty)

        pdfdoc = FancyDocTemplate(output,
                                 pageTemplates=[FP],
                                 showBoundary=0,
                                 pagesize=self.styles.ps,
                                 title=self.doc_title,
                                 author=self.doc_author,
                                 pageCompression=compressed
                                 )
        pdfdoc.multiBuild(elements)
        for fn in self.to_unlink:
            os.unlink(fn)


class TocBuilderVisitor(docutils.nodes.SparseNodeVisitor):

    def __init__(self, document):
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        self.toc = None

    def visit_reference(self, node):
        refid = node.attributes.get('refid')
        if refid:
            self.toc.refids.append(refid)


class FancyDocTemplate(BaseDocTemplate):

    def afterFlowable(self, flowable):
        if isinstance(flowable, OutlineEntry):
            # Notify TOC entry for headings/abstracts/dedications.
            level, text = flowable.level, flowable.text
            if hasattr(flowable, 'parent_id'):
                parent_id =  flowable.parent_id
            pagenum = self.page
            self.notify('TOCEntry', (level, text, pagenum, parent_id))


class FancyPage(PageTemplate):
    """ A page template that handles changing layouts.
    """

    def __init__(self,_id,head,foot,styles,smarty="0"):
        self.styles=styles
        self.head=head
        self.foot=foot
        self.smarty=smarty
        PageTemplate.__init__(self,_id,[])

    def beforeDrawPage(self,canv,doc):
        """Do adjustments to the page according to where we are in the document.

           * Gutter margins on left or right as needed

        """
        self.tw=self.styles.pw-self.styles.lm-self.styles.rm-self.styles.gm
        # What page template to use?
        tname=canv.__dict__.get('templateName',self.styles.firstTemplate)
        self.template=self.styles.pageTemplates[tname]

        doct = getattr(canv,'_doctemplate',None)
        canv._doctemplate = None # to make _listWrapOn work

        # Adjust text space accounting for header/footer
        head = self.template.get('showHeader',True) and (
            self.head or self.template.get('defaultHeader'))
        if head:
            if isinstance(head, list):
                head = head[:]
            else:
                head = [Paragraph(head,self.styles['header'])]
            _,self.hh=_listWrapOn(head,self.tw,canv)
        else:
            self.hh=0
        self.curHead = head
        foot = self.template.get('showFooter',True) and (
            self.foot or self.template.get('defaultFooter'))
        if foot:
            if isinstance(foot, list):
                foot = foot[:]
            else:
                foot = [Paragraph(foot,self.styles['footer'])]
            _,self.fh=_listWrapOn(foot,self.tw,canv)
        else:
            self.fh=0
        self.curFoot = foot

        canv._doctemplate = doct

        self.hx=self.styles.lm
        self.hy=self.styles.ph-self.styles.tm+self.styles.ts

        self.fx=self.styles.lm
        self.fy=self.styles.bm-self.styles.bs
        self.th=self.styles.ph-self.styles.tm-self.styles.bm-self.hh-self.fh

        # Adjust gutter margins
        if doc.page%2: # Left page
            x1=self.styles.lm
            y1=self.styles.tm+self.hh
        else: # Right page
            x1=self.styles.lm+self.styles.gm
            y1=self.styles.tm+self.hh

        self.frames=[]
        for frame in self.template['frames']:
            self.frames.append(SmartFrame(self,self.styles.adjustUnits(frame[0],self.tw)+x1,
                                          self.styles.adjustUnits(frame[1],self.th)+y1,
                                          self.styles.adjustUnits(frame[2],self.tw),
                                          self.styles.adjustUnits(frame[3],self.th)))

    def replaceTokens(self,elems,canv,doc):
        """Put doc_title/page number/etc in text of header/footer."""
        for e in elems:
            i=elems.index(e)
            if isinstance(e,Paragraph):
                text=e.text
                if not isinstance(text, unicode):
                    try:
                        text=unicode(text,e.encoding)
                    except AttributeError:
                        text=unicode(text,'utf-8')
                text=text.replace(u'###Page###',unicode(doc.page))
                text=text.replace(u"###Title###",doc.title)
                text=text.replace(u"###Section###",getattr(canv, 'sectName', ''))
                text=text.replace(u"###SectNum###",getattr(canv, 'sectNum', ''))
                text=smartyPants(text,self.smarty)
                elems[i]=Paragraph(text,e.style)

    def afterDrawPage(self,canv,doc):
        """Draw header/footer."""
        # Adjust for gutter margin
        if doc.page%2: # Left page
            hx=self.hx
            fx=self.fx
        else: # Right Page
            hx=self.hx+self.styles.gm
            fx=self.fx+self.styles.gm
        head = self.curHead
        if head:
            self.replaceTokens(head,canv,doc)
            container=_Container()
            container._content=head
            container.width=self.tw
            container.height=self.hh
            container.drawOn(canv,hx,self.hy)
        foot = self.curFoot
        if foot:
            self.replaceTokens(foot,canv,doc)
            container=_Container()
            container._content=foot
            container.width=self.tw
            container.height=self.fh
            container.drawOn(canv,fx,self.fy)

def main():
    '''Parse command line and call createPdf with the correct data'''

    parser = OptionParser()
    parser.add_option('-o', '--output',dest='output',metavar='FILE'
                      ,help='Write the PDF to FILE')

    def_ssheets=','.join([ os.path.expanduser(p) for p in \
    config.getValue("general","stylesheets","").split(',')])
    parser.add_option('-s', '--stylesheets',dest='style',metavar='STYLESHEETS',default=def_ssheets,
                      help='A comma-separated list of custom stylesheets. Default="%s"'%def_ssheets)

    def_sheetpath=':'.join([ os.path.expanduser(p) for p in \
        config.getValue("general","stylesheet_path","").split(':')])
    parser.add_option('--stylesheet-path',dest='stylepath',metavar='FOLDER:FOLDER:...:FOLDER',default=def_sheetpath,
                      help='A colon-separated list of folders to search for stylesheets. Default="%s"'%def_sheetpath)

    def_compressed=config.getValue("general","compressed",False)
    parser.add_option('-c', '--compressed',dest='compressed',action="store_true",default=def_compressed,
                      help='Create a compressed PDF. Default=%s'%def_compressed)

    parser.add_option('--print-stylesheet',dest='printssheet',action="store_true",default=False,
                      help='Print the default stylesheet and exit')

    parser.add_option('--font-folder',dest='ffolder',metavar='FOLDER',
                      help='Search this folder for fonts. (Deprecated)')

    def_fontpath=':'.join([ os.path.expanduser(p) for p in \
        config.getValue("general","font_path","").split(':')])
    parser.add_option('--font-path',dest='fpath',metavar='FOLDER:FOLDER:...:FOLDER',default=def_fontpath,
                      help='A colon-separated list of folders to search for fonts. Default="%s"'%def_fontpath)

    def_baseurl=None
    parser.add_option('--baseurl',dest='baseurl',metavar='URL',default=def_baseurl,
                      help='The base URL for relative URLs. Default="%s"'%def_baseurl)

    def_lang=config.getValue("general","language","en_US")
    parser.add_option('-l','--language',metavar='LANG',default=def_lang,dest='language',
                      help='Language to be used for hyphenation and docutils localizations.\
                      Default="%s"'%def_lang)

    def_header=config.getValue("general","header")
    parser.add_option('--header',metavar='HEADER',default=def_header,dest='header',
                      help='Page header if not specified in the document. Default="%s"'%def_header)
    def_footer=config.getValue("general","footer")
    parser.add_option('--footer',metavar='FOOTER',default=def_footer,dest='footer',
                      help='Page footer if not specified in the document. Default="%s"'%def_footer)


    def_smartquotes=config.getValue("general","smartquotes","0")
    parser.add_option("--smart-quotes",metavar="VALUE",default=def_smartquotes,dest="smarty",
                      help='Try to convert ASCII quotes, ellipsis and dashes to the typographically correct equivalent. For details, read the man page or the manual. Default="%s"'%def_smartquotes)

    def_fit=config.getValue("general","fit_mode","shrink")
    parser.add_option('--fit-literal-mode',metavar='MODE',default=def_fit,dest='fitMode',
                      help='What todo when a literal is too wide. One of error,overflow,shrink,truncate. Default="%s"'%def_fit)

    def_break=config.getValue("general","break_level",0)
    parser.add_option('-b','--break-level',dest='breaklevel',metavar='LEVEL',default=def_break,
                      help='Maximum section level that starts in a new page. Default: %d'%def_break)
    parser.add_option('--inline-links',action="store_true",dest='inlinelinks',default=False,
                      help='shows target between parenthesis instead of active link')
    parser.add_option('--repeat-table-rows',action="store_true",dest='repeattablerows',default=False,
                      help='Repeats header row for each splitted table')
    parser.add_option('-q','--quiet',action="store_true",dest='quiet',default=False,
                      help='Print less information.')
    parser.add_option('-v','--verbose',action="store_true",dest='verbose',default=False,
                      help='Print debug information.')
    parser.add_option('--very-verbose',action="store_true",dest='vverbose',default=False,
                      help='Print even more debug information.')
    parser.add_option('--version',action="store_true",dest='version',default=False,
                      help='Print version number and exit.')
    (options,args)=parser.parse_args()

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
        print open(os.path.join(abspath(dirname(__file__)),'styles','styles.json')).read()
        sys.exit(0)

    filename = False

    if len(args) == 0 or args[0]=='-':
        infile = sys.stdin
    elif len(args) > 1:
        log.critical('Usage: %s file.txt [ -o file.pdf ]', sys.argv[0])
        sys.exit(1)
    else:
        filename = args[0]
        infile=open(filename)

    if options.output:
        outfile=options.output
        if outfile =='-':
            outfile = sys.stdout
            options.compressed = False
            #we must stay quiet
            log.setLevel(logging.CRITICAL)
    else:
        if filename:
            if filename.endswith('.txt') or filename.endswith('.rst'):
                outfile = filename[:-4] + '.pdf'
            else:
                outfile=filename + '.pdf'
        else:
            outfile = sys.stdout
            options.compressed = False
            #we must stay quiet
            log.setLevel(logging.CRITICAL)
            #/reportlab/pdfbase/pdfdoc.py output can be a callable (stringio, stdout ...)

    if options.style:
        ssheet=options.style.split(',')
    else:
        ssheet=[]

    fpath=[]
    if options.fpath:
        fpath=options.fpath.split(':')
    if options.ffolder:
        fpath.append(options.ffolder)

    spath=[]
    if options.stylepath:
        spath=options.stylepath.split(':')

    RstToPdf(
        stylesheets=ssheet,
        language=options.language,
        header=options.header, footer=options.footer,
        inlinelinks=options.inlinelinks,
        breaklevel=int(options.breaklevel),
        baseurl=options.baseurl,
        fitMode=options.fitMode,
        smarty=str(options.smarty),
        fontPath=fpath,
        stylePath=spath,
        repeatTableRows=options.repeattablerows,
    ).createPdf(text=infile.read(),
                source_path=infile.name,
                output=outfile,
                compressed=options.compressed)

if __name__ == "__main__":
    main()
