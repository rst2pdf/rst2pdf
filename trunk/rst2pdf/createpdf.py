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
from docutils.transforms import Transformer
import docutils.readers.doctree
import docutils.core
import docutils.nodes

import pygments_code_block_directive

import reportlab
from reportlab.platypus import *
#from reportlab.platypus.para import Paragraph,FastPara,Para
from reportlab.pdfbase.pdfmetrics import stringWidth
import reportlab.lib.colors as colors
from reportlab.lib.enums import *
from reportlab.lib.units import *
from reportlab.lib.pagesizes import *

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

try:
    import wordaxe
    from wordaxe.PyHnjHyphenator import PyHnjHyphenator
    from wordaxe.rl.paragraph import Paragraph
    from wordaxe.rl.styles import ParagraphStyle, getSampleStyleSheet
    haveWordaxe=True
except ImportError:
    log.warning("No support for hyphenation, install wordaxe")
    haveWordaxe=False

class MyIndenter(Indenter):
    # Bugs in reportlab?
    def draw(self):
        pass
    width=0
    height=0

class RstToPdf(object):

    def __init__(self, stylesheets = [], language = 'en_US',breaklevel=1):
        self.lowerroman=['i','ii','iii','iv','v','vi','vii','viii','ix','x','xi']
        self.loweralpha=string.ascii_lowercase
        self.doc_title=None
        self.doc_author=None
        self.decoration = {'header':None, 'footer':None, 'endnotes':[]}
        stylesheets = [join(abspath(dirname(__file__)), 'styles.json')]+stylesheets
        self.styles=sty.StyleSheet(stylesheets)
        self.breaklevel=breaklevel

        # Load the hyphenators for all required languages
        if haveWordaxe:
            if not self.styles.languages:
                self.styles.languages=[language]
                self.styles['bodytext'].language=language
            for lang in self.styles.languages:
                try:
                    wordaxe.hyphRegistry[lang] = PyHnjHyphenator(lang,5)
                except ImportError: #PyHnj C extension is not installed
                    wordaxe.hyphRegistry[lang] = PyHnjHyphenator(lang,5,purePython=True)
            log.info('hyphenation by default in %s , loaded %s',
                self.styles['bodytext'].language, ','.join(self.styles.languages))

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
            print r
            return r
        except KeyError:
            log.warning('Unknown class %s', style)
            return None


    def gather_pdftext (self, node, depth, in_line_block=False,replaceEnt=True):
        return ''.join([self.gen_pdftext(n,depth,in_line_block,replaceEnt) for n in node.children ])

    def gen_pdftext(self, node, depth, in_line_block=False,replaceEnt=True):
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
            pre='<font face="%s">'%self.styles['code'].fontName
            post="</font>"
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
                if urlparse(uri)[0]:
                    pre+=u'<a href="%s" color="%s">'%(uri,self.styles.linkColor)
                    post='</a>'+post
            else:
                    uri=node.get('refid')
                    if uri:
                            pre+=u'<a href="#%s">'%uri
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
                log.warning(node)
            except (UnicodeDecodeError, UnicodeEncodeError):
                log.warning(repr(node))
            node.pdftext=self.gather_pdftext(node,depth)
            #print node.transform

        try:
            log.info("self.gen_pdftext: %s" % node.pdftext)
        except UnicodeDecodeError:
            pass
        return node.pdftext

    def gen_elements(self, node, depth, in_line_block=False, style=None):

        log.debug("gen_elements: %s", node.__class__)
        try:
            log.debug("gen_elements: %s", node)
        except (UnicodeDecodeError, UnicodeEncodeError):
            log.debug("gen_elements: %r", node)

        if style is None:
            style=self.styles['bodytext']

        if node['classes']:
            # Supports only one class, sorry ;-)
            try:
                style=self.styles[node['classes'][0]]
            except:
                log.info("Unknown class %s, using class bodytext.", node['classes'][0])

        if isinstance (node, docutils.nodes.document):
            node.elements=self.gather_elements(node,depth,style=style)

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

            for row in rows:
                r=[]
                for cell in row:
                    if isinstance(cell,str):
                        r.append("")
                    else:
                        r.append(self.gather_elements(cell,depth))
                data.append(r)

            st=spans+sty.tstyleNorm

            if hasHead:
                st+=[sty.tstyleHead(headRows)]

            # Colwidths in ReST are relative: 10,10,10 means 33%,33%,33%
            if colwidths:
                _tw=self.styles.tw/sum(colwidths)
                colwidths=[ w*_tw for w in colwidths ]
            else:
                colwidths = None # Auto calculate

            node.elements=[Table(data,colWidths=colwidths,style=TableStyle(st))]

        elif isinstance (node, docutils.nodes.title):
            # Special cases: (Not sure this is right ;-)
            if isinstance (node.parent, docutils.nodes.document):
                # FIXME maybe make it a coverpage?
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['title'])]
                self.doc_title=unicode(self.gen_pdftext(node,depth)).strip()
            elif isinstance (node.parent, docutils.nodes.topic):
                # FIXME style correctly
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['heading3'])]
            elif isinstance (node.parent, docutils.nodes.admonition) or \
                    isinstance (node.parent, docutils.nodes.sidebar) or \
                    isinstance (node.parent, docutils.nodes.table) :
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['heading3'])]
            else:
                # Section/Subsection/etc.
                text=self.gen_pdftext(node,depth)
                fch=node.children[0]
                if isinstance(fch,docutils.nodes.generated) and fch['classes']==['sectnum']:
                    snum=fch.astext()
                else:
                    snum=None
                key=node.get('refid')
                node.elements=[OutlineEntry(key,text,depth-1,snum),
                               Paragraph(text, self.styles['heading%d' % min(depth,3)])]
                if depth <=self.breaklevel:
                    node.elements.insert(0,PageBreak())


        elif isinstance (node, docutils.nodes.subtitle):
            if isinstance (node.parent,docutils.nodes.sidebar):
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['heading4'])]
            elif isinstance (node.parent,docutils.nodes.document):
                node.elements=[Paragraph(self.gen_pdftext(node,depth), self.styles['subtitle'])]

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
            # This is a tricky one. We need to switch our document's
            # page templates based on this. If decoration contains a
            # header and/or a footer, we need to use those
            # right now, we avoid trouble.
            # FIXME Implement
            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.header):
            self.decoration['header']=self.gather_pdftext(node,depth)
            node.elements=[]
        elif isinstance (node, docutils.nodes.footer):
            self.decoration['footer']=self.gather_pdftext(node,depth)
            node.elements=[]

        elif isinstance (node, docutils.nodes.author):
            if isinstance (node.parent,docutils.nodes.authors):
                # Is only one of multiple authors. Return a paragraph
                node.elements=[Paragraph(self.gather_pdftext(node,depth), style=style)]
            else:
                # A single author: works like a field
                fb=self.gather_pdftext(node,depth)
                node.elements=[Table([[Paragraph("Author:",style=self.styles['fieldname']),
                                    Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])]
                self.doc_author=fb.strip()

        elif isinstance (node, docutils.nodes.authors):
            # Multiple authors. Create a two-column table. Author references on the right.
            td=[[Paragraph("Authors:",style=self.styles['fieldname']),self.gather_elements(node,depth,style=style)]]
            node.elements=[Table(td,style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])]

        elif isinstance (node, docutils.nodes.organization):
            fb=self.gather_pdftext(node,depth)
            t=Table([[Paragraph("Organization:",style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.contact):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph("Contact:",style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.address):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph("Address:",style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.version):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph("Version:",style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.revision):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph("Revision:",style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.status):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph("Status:",style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.date):
            fb=self.gather_pdftext(node,depth)
            t=Table([[ Paragraph("Date:",style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]
        elif isinstance (node, docutils.nodes.copyright):
            fb=self.gather_pdftext(node,depth)
            t=Table([[Paragraph("Copyright:",style=self.styles['fieldname']),
                                Paragraph(fb,style) ]],style=sty.tstyles['field'],colWidths=[sty.fieldlist_lwidth,None])
            node.elements=[t]

        elif isinstance (node, docutils.nodes.topic)                                \
            or isinstance (node, docutils.nodes.field_body):
            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.section):
            node.elements=self.gather_elements(node,depth+1)

        elif isinstance (node, docutils.nodes.bullet_list)                   \
            or isinstance (node, docutils.nodes.enumerated_list)            \
            or isinstance (node, docutils.nodes.definition_list)            \
            or isinstance (node, docutils.nodes.option_list)                \
            or isinstance (node, docutils.nodes.field_list)                 \
            or isinstance (node, docutils.nodes.definition):

            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.option_list_item):

            optext = ', '.join([self.gather_pdftext(child,depth) for child in node.children[0].children])
            desc = self.gather_elements(node.children[1],depth,style)

            node.elements=[Table([[self.PreformattedFit(optext,self.styles["code"]),desc]],style=sty.tstyles['field'])]


        elif isinstance (node, docutils.nodes.definition_list_item):

            # I need to catch the classifiers here
            tt=[]
            dt=[]
            for n in node.children:
                if isinstance(n,docutils.nodes.term):
                    tt.append(self.styleToFont("definition_list_term")+self.gather_pdftext(n,depth,style)+"</font>")
                elif isinstance(n,docutils.nodes.classifier) :
                    tt.append(self.styleToFont("definition_list_classifier")+self.gather_pdftext(n,depth,style)+"</font>")
                else:
                    dt=dt+self.gen_elements(n,depth,style)

            node.elements=[Paragraph(' : '.join(tt),self.styles['definition_list_term']),
                           MyIndenter(left=10)]+dt+[MyIndenter(left=-10)]

        elif isinstance (node, docutils.nodes.list_item):
            # A list_item is a table of two columns.
            # The left one is the bullet itself, the right is the
            # item content. This way we can nest them.

            el=self.gather_elements(node,depth,style=style)
            b=""
            if node.parent.get('bullet') or isinstance(node.parent,docutils.nodes.bullet_list):
                b=node.parent.get('bullet')
                if b=="None":
                    b=""

            elif node.parent.get ('enumtype')=='arabic':
                b=str(node.parent.children.index(node)+1)+'.'

            elif node.parent.get ('enumtype')=='lowerroman':
                b=str(self.lowerroman[node.parent.children.index(node)])+'.'

            elif node.parent.get ('enumtype')=='upperroman':
                b=str(self.lowerroman[node.parent.children.index(node)].upper())+'.'

            elif node.parent.get ('enumtype')=='loweralpha':
                b=str(self.loweralpha[node.parent.children.index(node)])+'.'
            elif node.parent.get ('enumtype')=='upperalpha':
                b=str(self.loweralpha[node.parent.children.index(node)].upper())+'.'
            else:
                log.critical("Unknown kind of list_item %s", node.parent)
                sys.exit(1)
            # FIXME: use different unicode bullets depending on b
            if b and b in "*+-":
                b=u'\u2022'

            el[0].bulletText = b
            for e in el[1:]:
                e.bulletText=" "
            node.elements=[Table([[el]],style=sty.tstyles["bullet"])]

        elif isinstance (node, docutils.nodes.transition):
            node.elements=[Separation()]


        elif isinstance (node, docutils.nodes.system_message)     \
            or isinstance (node, docutils.nodes.problematic):
            # FIXME show the error in the document, red, whatever
            log.warning("Problematic node %s", node.astext())
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
            or isinstance (node, docutils.nodes.caution)            \
            or isinstance (node, docutils.nodes.danger)             \
            or isinstance (node, docutils.nodes.error)                \
            or isinstance (node, docutils.nodes.hint)                 \
            or isinstance (node, docutils.nodes.important)        \
            or isinstance (node, docutils.nodes.note)                 \
            or isinstance (node, docutils.nodes.tip)                    \
            or isinstance (node, docutils.nodes.warning)            \
            or isinstance (node, docutils.nodes.admonition):
            node.elements=[Paragraph(node.tagname.title(),style=self.styles['heading3'])]+self.gather_elements(node,depth,style=style)

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
                img=PILImage.open(imgname)
                iw,ih=img.size
            except NameError: # No PIL
                 # FIXME: surely we can do better than this ;-)
                 # but this only means that image sizes specified
                 # in % or unspecified will probably be broken.
                 iw=None
                 ih=None


            # Assume a DPI of 300, which is pretty much made up,
            # and then a 100% size would be iw*inch/300, so we pass
            # that as the second parameter to adjustUnits

            w=node.get('width')
            if w is not None:
                if iw:
                    w=sty.adjustUnits(w,iw*inch/300)
                else:
                    w=sty.adjustUnits(w,self.styles.pw*.5)
            else:
                log.warning("Using image %s without specifying size."
                    "Calculating based on 300dpi", imgname)
                # No width specified at all. Make it up
                # as if we knew what we're doing
                if iw:
                    w=iw*inch/300

            h=node.get('height')
            if h is not None:
                if ih:
                    h=sty.adjustUnits(h,ih*inch/300)
                else:
                    h=sty.adjustUnits(h,self.styles.ph*.5)
            else:
                # Now, often, only the width is specified!
                # if we don't have a height, we need to keep the
                # aspect ratio, or else it will look ugly
                if iw:
                    h=w*ih/iw

            # And now we have this probably completely bogus size!
            log.info("Image %s size calculated:  %fcm by %fcm",
                imgname, w/cm, h/cm)

            i=Image(filename=imgname,
                    height=h,
                    width=w)
            if node.get('align'):
                i.hAlign=node.get('align').upper()
            else:
                i.hAlign='CENTER'
            node.elements=[i]

        elif isinstance (node, docutils.nodes.figure):
            # The sub-elements are the figure and the caption, and't ugly if
            # they separate
            node.elements=[KeepTogether(self.gather_elements(node,depth,style=self.styles["figure"]))]

        elif isinstance (node, docutils.nodes.caption):
            node.elements=[Paragraph('<i>'+self.gather_pdftext(node,depth)+'</i>',style=style)]

        elif isinstance (node, docutils.nodes.legend):
            node.elements=self.gather_elements(node,depth,style=style)

        elif isinstance (node, docutils.nodes.sidebar):
            node.elements=[Table([[ self.gather_elements(node,depth,style=style)]],style=sty.tstyles['sidebar'])]

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
                log.error(node)
            except (UnicodeDecodeError, UnicodeEncodeError):
                log.debug(repr(node))
            node.elements=self.gather_elements(node,depth,style)
            #sys.exit(1)

        # set anchors for internal references
        for id in node['ids']:
            node.elements.insert(
                    # FIXME: WTF does this do?
                    node.elements and isinstance(node.elements[0], PageBreak) and 1 or 0,
                    Paragraph('<a name="%s"/>'%id,style))

        try:
            log.debug("gen_elements: %s", node.elements)
        except: # unicode problems FIXME: explicit error
            pass
        return node.elements

    def gather_elements (self,node, depth, in_line_block=False,style=None):
        if style is None:
            style=self.styles['bodytext']
        r=[]
        for n in node.children:
            #import pdb; pdb.set_trace()
            r.extend(self.gen_elements(n,depth,in_line_block,style=style))
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
        # FIXME: make it scale correctly
        w=max(map(lambda line:stringWidth(line,style.fontName,style.fontSize),text.splitlines()))
        mw=self.styles.tw-style.leftIndent-style.rightIndent
        if w>mw:
            style=copy(style)
            f=max((0.375,mw/w))
            #style.fontSize*=f
            #style.leading*=f
        return XPreformatted(text,style)

    def createPdf(self,text=None,output=None,doctree=None,compressed=False):
        '''Create a PDF from text (ReST input), or doctree (docutil nodes)
        and save it in outfile.

        If outfile is a string, it's a filename.
        If it's something with a write method, (like a StringIO,
        or a file object), the data is saved there.

        '''


        if not doctree:
            if text:
                doctree=docutils.core.publish_doctree(text)
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
        FP=FancyPage("fancypage",self.styles.pw,self.styles.ph,self.styles.tm,
                                 self.styles.bm,self.styles.lm,self.styles.rm,
                                 self.styles.gm,head,foot,self.styles)

        pdfdoc = BaseDocTemplate(output,
                                 pageTemplates=[FP],
                                 showBoundary=0,
                                 pagesize=self.styles.ps,
                                 title=self.doc_title,
                                 author=self.doc_author,
                                 pageCompression=compressed
                                 )
        pdfdoc.build(elements)


class OutlineEntry(Flowable):
    def __init__(self,label,text,level=0,snum=None):
        '''* label is a unique label.
           * text is the text to be displayed in the outline tree
           * level is the level, 0 is outermost, 1 is child of 0, etc.
        '''
        if label is None: # it happens
            self.label=text.replace(u'\xa0', ' ').strip(
                ).replace(' ', '_').encode('ascii', 'replace')
        else:
            self.label=label.strip()
        self.text=text.strip()
        self.level=int(level)
        self.snum=snum
        Flowable.__init__(self)

    def wrap(self,w,h):
        '''This takes no space'''
        return (0,0)

    def draw(self):
        self.canv.bookmarkPage(self.label)
        self.canv.sectName=self.text
        if self.snum is not None:
            self.canv.sectNum=self.snum
        else:
            self.canv.sectNum=""
        self.canv.addOutlineEntry(self.text,
                                  self.label,
                                  self.level, False)

    def __repr__(self):
        return "OutlineEntry (label=%s , text=%s , level=%d) \n"%(self.label,self.text,self.level)

class Separation(Flowable):
    """A simple <hr>-like flowable"""

    def wrap(self,w,h):
        self.w=w
        return (w,1*cm)

    def draw(self):
        self.canv.line(0,0.5*cm,self.w,0.5*cm)


class FancyPage(PageTemplate):
    """ A page template that handles changing layouts.
    """
    def __init__(self,_id,pw,ph,tm,bm,lm,rm,gm,head,foot,styles):

        self.styles=styles
        tw=pw-lm-rm-gm

        if head:
            hh=Paragraph(head,style=self.styles['header']).wrap(tw,ph)[1]
        else:
            hh=0
        if foot:
            fh=Paragraph(foot,style=self.styles['footer']).wrap(tw,ph)[1]
        else:
            fh=0

        #textframe=Frame(lm,tm+hh,tw,ph-tm-bm-hh-fh,topPadding=hh,bottomPadding=fh)

        self.head=head
        self.hx=lm
        self.hy=ph-tm

        self.foot=foot
        self.fx=lm
        self.fy=bm
        self.tw=tw
        self.ph=ph
        self.gm=gm
        self.lm=lm
        self.tm=tm
        self.hh=hh
        self.fh=fh
        self.bm=bm

        PageTemplate.__init__(self,_id,[])

    def beforeDrawPage(self,canv,doc):
        '''Do adjustments to the page according to where we are in the document.

           * Gutter margins on left or right as needed

           * Put doc_title or page number in header/footer

        '''

        # Adjust gutter margins
        if doc.page%2: # Left page
            textframe=Frame(self.lm,self.tm+self.hh,self.tw,
                            self.ph-self.tm-self.bm-self.hh-self.fh,
                            topPadding=self.hh,bottomPadding=self.fh)
        else: # Right page
            textframe=Frame(self.lm+self.gm,self.tm+self.hh,self.tw,
                            self.ph-self.tm-self.bm-self.hh-self.fh,
                            topPadding=self.hh,bottomPadding=self.fh)



        self.frames=[textframe]

    def replaceTokens(self,text,canv,doc):
        text=text.replace('###Page###',str(doc.page))
        text=text.replace("###Title###",doc.title)
        # FIXME: make this nicer
        try:
            text=text.replace("###Section###",canv.sectName)
        except AttributeError:
            text=text.replace("###Section###",'')
        try:
            text=text.replace("###SectNum###",canv.sectNum)
        except AttributeError:
            text=text.replace("###SectNum###",'')
        return text

    def afterDrawPage(self,canv,doc):
        # Adjust gutter margins
        if doc.page%2: # Left page
            hx=self.hx
            fx=self.fx
        else: # Right Page
            hx=self.hx+self.gm
            fx=self.fx+self.gm

        if self.head:
            head=self.replaceTokens(self.head,canv,doc)
            para=Paragraph(head,style=self.styles['header'])
            para.wrap(self.tw,self.ph)
            para.drawOn(canv,hx,self.hy)
        if self.foot:
            foot=self.replaceTokens(self.foot,canv,doc)
            para=Paragraph(foot,style=self.styles['footer'])
            para.wrap(self.tw,self.ph)
            para.drawOn(canv,fx,self.fy)


def main():
    '''Parse command line and call createPdf with the correct data'''

    parser = OptionParser()
    parser.add_option('-o', '--output',dest='output',metavar='FILE'
                      ,help='Write the PDF to FILE')
    parser.add_option('-s', '--stylesheets',dest='style',metavar='STYLESHEETS',
                      help='A comma-separated list of custom stylesheets')
    parser.add_option('-c', '--compressed',dest='compressed',action="store_true",default=False,
                      help='Create a compressed PDF')
    parser.add_option('--print-stylesheet',dest='printssheet',action="store_true",default=False,
                      help='Print the default stylesheet and exit')
    parser.add_option('--font-folder',dest='ffolder',metavar='FOLDER',
                      help='Search this folder for fonts.')
    parser.add_option('-l','--language',metavar='LANG',default='en_US',
                      help='Language to be used for hyphenation.')
    parser.add_option('-b','--break-level',dest='breaklevel',metavar='LEVEL',default='1',
                      help='Maximum section level that starts in a new page. Default: 1')
    parser.add_option('-q','--quiet',action="store_true",dest='quiet',default=False,
                      help='Print less information.')
    parser.add_option('-v','--verbose',action="store_true",dest='verbose',default=False,
                      help='Print debug information.')
    parser.add_option('--very-verbose',action="store_true",dest='vverbose',default=False,
                      help='Print even more debug information.')
    (options,args)=parser.parse_args()

    if options.quiet:
        log.setLevel(logging.CRITICAL)

    if options.verbose:
        log.setLevel(logging.INFO)

    if options.vverbose:
        log.setLevel(logging.DEBUG)

    if options.printssheet:
        print open(join(abspath(dirname(__file__)), 'styles.json')).read()
        sys.exit(0)

    if len(args) <> 1:
        log.critical('Usage: %s file.txt [ -o file.pdf ]', sys.argv[0])
        sys.exit(1)

    infile=args[0]
    if options.output:
        outfile=options.output
    else:
        if infile.endswith('.txt') or infile.endswith('.rst'):
            outfile = infile[:-4] + '.pdf'
        else:
            outfile=infile + '.pdf'

    if options.ffolder:
        TTFSearchPath.append(ffolder)

    if options.style:
        ssheet=options.style.split(',')
    else:
        ssheet=[]

    RstToPdf(stylesheets = ssheet,
             language=options.language,
             breaklevel=int(options.breaklevel)).createPdf(text=open(infile).read(),
                                                  output=outfile,
                                                  compressed=options.compressed)


if __name__ == "__main__":
    main()
