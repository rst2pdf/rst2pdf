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


import os
import tempfile
from copy import copy

import docutils.nodes
import reportlab

from svgimage import SVGImage
from math_directive import math_node
from math_flowable import Math
from aafigure_directive import Aanode

from log import log, nodeid
from utils import log, parseRaw
from reportlab.platypus import Paragraph, TableStyle
from reportlab.lib.units import cm
from flowables import Table, DelayedTable, SplitTable, Heading, \
              Spacer, MyIndenter, MyImage, MyTableOfContents, \
              Separation, BoxedContainer, BoundByWidth

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


class TocBuilderVisitor(docutils.nodes.SparseNodeVisitor):

    def __init__(self, document):
        docutils.nodes.SparseNodeVisitor.__init__(self, document)
        self.toc = None
        # For some reason, when called via sphinx,
        # .. contents:: ends up trying to call
        # visitor.document.reporter.debug
        # so we need a valid document here.
        self.document=docutils.utils.new_document('')

    def visit_reference(self, node):
        refid = node.attributes.get('refid')
        if refid:
            self.toc.refids.append(refid)




# These are to suppress repeated messages
unkn_elem=set()

def dispatch(client, node, style=None):
        log.debug("gen_elements: %s", node.__class__)
        log.debug("[%s]", nodeid(node))
        try:
            log.debug("gen_elements: %s", node)
        except (UnicodeDecodeError, UnicodeEncodeError):
            log.debug("gen_elements: %r", node)

        # set anchors for internal references
        try:
            for i in node['ids']:
                client.pending_targets.append(i)
        except TypeError: #Happens with docutils.node.Text
            pass


        try:
            if node['classes'] and node['classes'][0]:
                # FIXME: Supports only one class, sorry ;-)
                if client.styles.StyleSheet.has_key(node['classes'][0]):
                    style = client.styles[node['classes'][0]]
                else:
                    log.info("Unknown class %s, ignoring. [%s]",
                        node['classes'][0], nodeid(node))
        except TypeError: # Happens when a docutils.node.Text reaches here
            pass

        if style is None or style == client.styles['bodytext']:
            style = client.styles.styleForNode(node)

        if isinstance(node, docutils.nodes.document):
            node.elements = client.gather_elements(node, style=style)

        elif HAS_SPHINX and isinstance(node, (sphinx.addnodes.glossary,
                                              sphinx.addnodes.start_of_file)):
            node.elements = client.gather_elements(node, style=style)

        elif HAS_SPHINX and isinstance(node, (sphinx.addnodes.index)):
            try:
                client.pending_targets.append(node['entries'][0][2])
            except IndexError:
                if node['entries']:
                    log.error("Can't process index entry: %s [%s]",
                        node['entries'], nodeid(node))
            node.elements = []

        elif isinstance(node, math_node):
            node.elements = [Math(node.math_data)]

        #######################
        ## Tables
        #######################

        elif isinstance(node, docutils.nodes.table):
            node.elements = [Spacer(0, client.styles['table'].spaceBefore)] + \
                            client.gather_elements(node, style=style) +\
                            [Spacer(0, client.styles['table'].spaceAfter)]

        elif isinstance(node, docutils.nodes.tgroup):
            rows = []
            colWidths = []
            hasHead = False
            headRows = 0
            for n in node.children:
                if isinstance(n, docutils.nodes.thead):
                    hasHead = True
                    for row in n.children:
                        r = []
                        for cell in row.children:
                            r.append(cell)
                        rows.append(r)
                    headRows = len(rows)
                elif isinstance(n, docutils.nodes.tbody):
                    for row in n.children:
                        r = []
                        for cell in row.children:
                            r.append(cell)
                        rows.append(r)
                elif isinstance(n, docutils.nodes.colspec):
                    colWidths.append(int(n['colwidth']))

            # colWidths are in no specific unit, really. Maybe ems.
            # Convert them to %
            colWidths=map(int, colWidths)
            tot=sum(colWidths)
            colWidths=["%s%%"%((100.*w)/tot) for w in colWidths]

            if 'colWidths' in style.__dict__:
                colWidths[:len(style.colWidths)]=style.colWidths

            spans = client.filltable(rows)

            data = []
            cellStyles = []
            rowids = range(0, len(rows))
            for row, i in zip(rows, rowids):
                r = []
                j = 0
                for cell in row:
                    if isinstance(cell, str):
                        r.append("")
                    else:
                        # I honestly have no idea what the next line does
                        # (Roberto Alsina, May 25th, 2009)
                        ell = client.gather_elements(cell, style=
                            i < headRows and client.styles['table-heading'] \
                            or style)
                        #if len(ell) == 1:
                            # Experiment: if the cell has a single element,
                            # extract its  class and use it for the cell.
                            # That way, you can have cells with specific
                            # background colors, at least.
                            #
                            # Experiment killed ;-)
                            # You can do that and more using table styles now!
                            #try:
                                #cellStyles += \
                                    #client.styles.pStyleToTStyle(ell[0].style,
                                                               #j, i)
                            ## Fix for issue 85: only do it if it has a style.
                            #except AttributeError:
                                #pass
                        r.append(ell)
                    j += 1
                data.append(r)

            st = TableStyle(spans)
            if 'commands' in client.styles['table'].__dict__:
                for cmd in client.styles['table'].commands:
                    st.add(*cmd)
            if 'commands' in style.__dict__:
                for cmd in style.commands:
                    st.add(*cmd)
            for cmd in cellStyles:
                st.add(*cmd)

            if hasHead:
                for cmd in client.styles.tstyleHead(headRows):
                    st.add(*cmd)
            rtr = client.repeat_table_rows

            node.elements = [DelayedTable(data, colWidths, st, rtr)]

        elif isinstance(node, docutils.nodes.title):
            # Special cases: (Not sure this is right ;-)
            if isinstance(node.parent, docutils.nodes.document):
                node.elements = [Paragraph(client.gen_pdftext(node),
                                           client.styles['title'])]
                client.doc_title = unicode(client.gen_pdftext(node)).strip()
            elif isinstance(node.parent, docutils.nodes.topic):
                node.elements = [Paragraph(client.gen_pdftext(node),
                                           client.styles['topic-title'])]
            elif isinstance(node.parent, docutils.nodes.Admonition):
                node.elements = [Paragraph(client.gen_pdftext(node),
                                           client.styles['admonition-title'])]
            elif isinstance(node.parent, docutils.nodes.table):
                node.elements = [Paragraph(client.gen_pdftext(node),
                                           client.styles['table-title'])]
            elif isinstance(node.parent, docutils.nodes.sidebar):
                node.elements = [Paragraph(client.gen_pdftext(node),
                                           client.styles['sidebar-title'])]
            else:
                # Section/Subsection/etc.
                text = client.gen_pdftext(node)
                fch = node.children[0]
                if isinstance(fch, docutils.nodes.generated) and \
                    fch['classes'] == ['sectnum']:
                    snum = fch.astext()
                else:
                    snum = None
                key = node.get('refid')
                maxdepth=4
                if reportlab.Version > '2.1':
                    maxdepth=6
                    
                # The parent ID is the refid + an ID to make it unique for Sphinx
                parent_id=(node.parent.get('ids', [None]) or [None])[0]+u'-'+unicode(id(node))
                node.elements = [ Heading(text,
                        client.styles['heading%d'%min(client.depth, maxdepth)],
                        level=client.depth-1,
                        parent_id=parent_id,
                        node=node
                        )]
                if client.depth <= client.breaklevel:
                    node.elements.insert(0, MyPageBreak(breakTo=client.breakside))

        elif isinstance(node, docutils.nodes.subtitle):
            if isinstance(node.parent, docutils.nodes.sidebar):
                node.elements = [Paragraph(client.gen_pdftext(node),
                    client.styles['sidebar-subtitle'])]
            elif isinstance(node.parent, docutils.nodes.document):
                node.elements = [Paragraph(client.gen_pdftext(node),
                    client.styles['subtitle'])]

        elif HAS_SPHINX and isinstance(node,
                sphinx.addnodes.compact_paragraph):
            node.elements = client.gather_elements(node, style=style)

        elif HAS_SPHINX and isinstance(node,sphinx.addnodes.module):
            node.elements = [Reference('module-'+node['modname'])]

        elif isinstance(node, docutils.nodes.paragraph):
            node.elements = [Paragraph(client.gen_pdftext(node), style)]

        elif isinstance(node, docutils.nodes.docinfo):
            # A docinfo usually contains several fields.
            # We'll render it as a series of elements, one field each.

            node.elements = client.gather_elements(node, style=style)

        elif isinstance(node, docutils.nodes.field):
            # A field has two child elements, a field_name and a field_body.
            # We render as a two-column table, left-column is right-aligned,
            # bold, and much smaller

            fn = Paragraph(client.gather_pdftext(node.children[0]) + ":",
                style=client.styles['fieldname'])
            fb = client.gen_elements(node.children[1],
                 style=client.styles['fieldvalue'])
            t_style=TableStyle(client.styles['field_list'].commands)
            node.elements = [DelayedTable([[fn, fb]], style=t_style,
                colWidths=client.styles['field_list'].colWidths)]

        elif isinstance(node, docutils.nodes.decoration):
            node.elements = client.gather_elements(node, style=style)

        elif isinstance(node, docutils.nodes.header):
            client.decoration['header'] = client.gather_elements(node,
                style=client.styles['header'])
            node.elements = []
        elif isinstance(node, docutils.nodes.footer):
            client.decoration['footer'] = client.gather_elements(node,
                style=client.styles['footer'])
            node.elements = []

        elif isinstance(node, docutils.nodes.author):
            if isinstance(node.parent, docutils.nodes.authors):
                # Is only one of multiple authors. Return a paragraph
                node.elements = [Paragraph(client.gather_pdftext(node),
                    style=style)]
                if client.doc_author:
                    client.doc_author += client.author_separator(style=style) \
                        + node.astext().strip()
                else:
                    client.doc_author = node.astext().strip()
            else:
                # A single author: works like a field
                fb = client.gather_pdftext(node)

                t_style=TableStyle(client.styles['field_list'].commands)
                colWidths=map(client.styles.adjustUnits,
                    client.styles['field_list'].colWidths)

                node.elements = [Table(
                    [[Paragraph(client.text_for_label("author", style),
                        style=client.styles['fieldname']),
                      Paragraph(fb, style)]],
                    style=t_style, colWidths=colWidths)]
                client.doc_author = node.astext().strip()

        elif isinstance(node, docutils.nodes.authors):
            # Multiple authors. Create a two-column table.
            # Author references on the right.
            t_style=TableStyle(client.styles['field_list'].commands)
            colWidths = client.styles['field_list'].colWidths

            td = [[Paragraph(client.text_for_label("authors", style),
                        style=client.styles['fieldname']),
                   client.gather_elements(node, style=style)]]
            node.elements = [DelayedTable(td, style=t_style,
                colWidths=colWidths)]

        elif isinstance(node, docutils.nodes.organization):
            fb = client.gather_pdftext(node)
            t_style=TableStyle(client.styles['field_list'].commands)
            colWidths=client.styles['field_list'].colWidths
            label=client.text_for_label("organization", style)
            t = DelayedTable([[Paragraph(label, style=client.styles['fieldname']),
                        Paragraph(fb, style)]],
                        style=t_style, colWidths=colWidths)
            node.elements = [t]
        elif isinstance(node, docutils.nodes.contact):
            fb = client.gather_pdftext(node)
            t_style=TableStyle(client.styles['field_list'].commands)
            colWidths= client.styles['field_list'].colWidths
            label=client.text_for_label("contact", style)
            t = DelayedTable([[Paragraph(label, style=client.styles['fieldname']),
                        Paragraph(fb, style)]],
                        style=t_style, colWidths=colWidths)
            node.elements = [t]
        elif isinstance(node, docutils.nodes.address):
            fb = client.gather_pdftext(node)
            t_style=TableStyle(client.styles['field_list'].commands)
            colWidths= client.styles['field_list'].colWidths
            label=client.text_for_label("address", style)
            t = DelayedTable([[Paragraph(label, style=client.styles['fieldname']),
                        Paragraph(fb, style)]],
                        style=t_style, colWidths=colWidths)
            node.elements = [t]
        elif isinstance(node, docutils.nodes.version):
            fb = client.gather_pdftext(node)
            t_style=TableStyle(client.styles['field_list'].commands)
            colWidths= client.styles['field_list'].colWidths
            label=client.text_for_label("version", style)
            t = DelayedTable([[Paragraph(label, style=client.styles['fieldname']),
                        Paragraph(fb, style)]],
                        style=t_style, colWidths=colWidths)
            node.elements = [t]
        elif isinstance(node, docutils.nodes.revision):
            fb = client.gather_pdftext(node)
            t_style=TableStyle(client.styles['field_list'].commands)
            colWidths=map(client.styles.adjustUnits,
                client.styles['field_list'].colWidths)
            label=client.text_for_label("revision", style)
            t = Table([[Paragraph(label, style=client.styles['fieldname']),
                        Paragraph(fb, style)]],
                        style=t_style, colWidths=colWidths)
            node.elements = [t]
        elif isinstance(node, docutils.nodes.status):
            fb = client.gather_pdftext(node)
            t_style=TableStyle(client.styles['field_list'].commands)
            colWidths= client.styles['field_list'].colWidths
            label=client.text_for_label("status", style)
            t = DelayedTable([[Paragraph(label, style=client.styles['fieldname']),
                        Paragraph(fb, style)]],
                        style=t_style, colWidths=colWidths)
            node.elements = [t]
        elif isinstance(node, docutils.nodes.date):
            fb = client.gather_pdftext(node)
            t_style = TableStyle(client.styles['field_list'].commands)
            colWidths = client.styles['field_list'].colWidths
            label = client.text_for_label("date", style)
            t = DelayedTable([[Paragraph(label, style = client.styles['fieldname']),
                        Paragraph(fb, style)]],
                        style=t_style, colWidths = colWidths)
            node.elements = [t]
        elif isinstance(node, docutils.nodes.copyright):
            fb = client.gather_pdftext(node)
            t_style = TableStyle(client.styles['field_list'].commands)
            colWidths = client.styles['field_list'].colWidths
            label = client.text_for_label("copyright", style)
            t = DelayedTable([[Paragraph(label, style=client.styles['fieldname']),
                        Paragraph(fb, style)]],
                        style=t_style, colWidths=colWidths)
            node.elements = [t]

        elif isinstance(node, docutils.nodes.topic):
            # toc
            node_classes = node.attributes.get('classes', [])
            if 'contents' in node_classes:
                toc_visitor = TocBuilderVisitor(node.document)
                if 'local' in node_classes:
                    toc_visitor.toc = MyTableOfContents(parent=node.parent)
                else:
                    toc_visitor.toc = MyTableOfContents(parent=None)
                toc_visitor.toc.linkColor = client.styles.linkColor
                node.walk(toc_visitor)
                toc = toc_visitor.toc
                toc.levelStyles=[client.styles['toc%d'%l] for l in range(1,15)]
                for s in toc.levelStyles:
                    # FIXME: awful slimy hack!
                    s.__class__=reportlab.lib.styles.ParagraphStyle
                ## Issue 117: add extra TOC levelStyles.
                ## 9-deep should be enough.
                #for i in range(4):
                    #ps = toc.levelStyles[-1].__class__(name='Level%d'%(i+5),
                         #parent=toc.levelStyles[-1],
                         #leading=toc.levelStyles[-1].leading,
                         #firstlineIndent=toc.levelStyles[-1].firstLineIndent,
                         #leftIndent=toc.levelStyles[-1].leftIndent+1*cm)
                    #toc.levelStyles.append(ps)

                ## Override fontnames (defaults to Times-Roman)
                #for levelStyle in toc.levelStyles:
                    #levelStyle.__dict__['fontName'] = \
                        #client.styles['tableofcontents'].fontName
                if 'local' in node_classes:
                    node.elements = [toc]
                else:
                    node.elements = \
                        [Paragraph(client.gen_pdftext(node.children[0]),
                        client.styles['heading1']), toc]
            else:
                node.elements = client.gather_elements(node, style=style)

        elif isinstance(node, docutils.nodes.field_body):
            node.elements = client.gather_elements(node, style=style)

        elif isinstance(node, docutils.nodes.section):
            client.depth+=1
            node.elements = client.gather_elements(node)
            client.depth-=1

        elif isinstance(node, docutils.nodes.bullet_list):
            node._bullSize = client.styles["enumerated_list_item"].leading
            node.elements = client.gather_elements(node,
                style=client.styles["bullet_list_item"])
            s = client.styles["bullet_list"]
            if s.spaceBefore:
                node.elements.insert(0, Spacer(0, s.spaceBefore))
            if s.spaceAfter:
                node.elements.append(Spacer(0, s.spaceAfter))

        elif isinstance(node, (docutils.nodes.definition_list,
                docutils.nodes.option_list)):

            node.elements = client.gather_elements(node, style=style)


        elif isinstance(node, docutils.nodes.field_list):

            node.elements = [Spacer(0,client.styles['field_list'].spaceBefore)]+\
                client.gather_elements(node, style=style)

        elif isinstance(node, docutils.nodes.enumerated_list):
            node._bullSize = client.styles["enumerated_list_item"].leading*\
                max([len(client.bullet_for_node(x)[0]) for x in node.children])
            node.elements = client.gather_elements(node,
                style = client.styles["enumerated_list_item"])
            s = client.styles["enumerated_list"]
            if s.spaceBefore:
                node.elements.insert(0, Spacer(0, s.spaceBefore))
            if s.spaceAfter:
                node.elements.append(Spacer(0, s.spaceAfter))

        elif isinstance(node, docutils.nodes.definition):
            node.elements = client.gather_elements(node,
                                style = client.styles["definition"])

        elif isinstance(node, docutils.nodes.option_list_item):

            optext = ', '.join([client.gather_pdftext(child)
                    for child in node.children[0].children])

            desc = client.gather_elements(node.children[1], style)

            t_style = TableStyle(client.styles['option_list'].commands)
            colWidths = client.styles['option_list'].colWidths
            node.elements = [DelayedTable([[client.PreformattedFit(
                optext, client.styles["literal"]), desc]], style = t_style,
                colWidths = colWidths)]


        elif isinstance(node, docutils.nodes.definition_list_item):
            # I need to catch the classifiers here
            tt = []
            dt = []
            ids = []
            for n in node.children:
                if isinstance(n, docutils.nodes.term):
                    for i in n['ids']: # Used by sphinx glossary lists
                        if i not in client.targets:
                            ids.append('<a name="%s"/>' % i)
                            client.targets.append(i)
                    tt.append(client.styleToFont("definition_list_term")
                        + client.gather_pdftext(n) + "</font>")
                elif isinstance(n, docutils.nodes.classifier):
                    tt.append(client.styleToFont("definition_list_classifier")
                        + client.gather_pdftext(n) + "</font>")
                else:
                    dt.extend(client.gen_elements(n, style))
            node.elements = [Paragraph(''.join(ids)+' : '.join(tt),
                client.styles['definition_list_term']),
                MyIndenter(left=10)] + dt + [MyIndenter(left=-10)]

        elif isinstance(node, docutils.nodes.list_item):
            el = client.gather_elements(node, style=style)
            

            b, t = client.bullet_for_node(node)

            # FIXME: this is really really not good code
            if not el:
                el = [Paragraph(u"<nobr>\xa0</nobr>", client.styles["bodytext"])]

            # FIXME: use different unicode bullets depending on b
            if b and b in "*+-":
                b = u'\u2022'

            bStyle = copy(style)
            bStyle.alignment = 2

            if t == 'bullet':
                st=client.styles['bullet_list']
                item_st=client.styles['bullet_list_item']
            else:
                st=client.styles['item_list']
                item_st=client.styles['item_list_item']
                
            idx=node.parent.children.index(node)
            if idx>0: # Not the first item
                sb=item_st.spaceBefore
            else:
                sb=0
                
            if (idx+1)<len(node.parent.children): #Not the last item
                sa=item_st.spaceAfter
            else:
                sa=0
                
            t_style = TableStyle(st.commands)

            #colWidths = map(client.styles.adjustUnits,
                #client.styles['item_list'].colWidths)
            colWidths = st.colWidths

            if client.splittables:
                node.elements = [Spacer(0,sb),
                                 SplitTable([[Paragraph(b, style = bStyle), el]],
                                 style = t_style,
                                 colWidths = colWidths),
                                 Spacer(0,sa)
                                 ]
            else:
                node.elements = [Spacer(0,sb),
                                 DelayedTable([[Paragraph(b, style = bStyle), el]],
                                 style = t_style,
                                 colWidths = colWidths),
                                 Spacer(0,sa)
                                 ]

        elif isinstance(node, docutils.nodes.transition):
            node.elements = [Separation()]


        elif isinstance(node, (docutils.nodes.system_message,
                               docutils.nodes.problematic)):
            # FIXME show the error in the document, red, whatever
            # log.warning("Problematic node %s", node.astext())
            node.elements = []

        elif isinstance(node, docutils.nodes.block_quote):
            # This should work, but doesn't look good inside of
            # table cells (see Issue 173)
            #node.elements = [MyIndenter(left=client.styles['blockquote'].leftIndent)]\
                #+ client.gather_elements( node, style) + \
                #[MyIndenter(left=-client.styles['blockquote'].leftIndent)]
            # Workaround for Issue 173 using tables
            leftIndent=client.styles['blockquote'].leftIndent
            rightIndent=client.styles['blockquote'].rightIndent
            spaceBefore=client.styles['blockquote'].spaceBefore
            spaceAfter=client.styles['blockquote'].spaceAfter
            data=[['',client.gather_elements( node, style)]]
            if client.splittables:
                node.elements=[Spacer(0,spaceBefore),SplitTable(data,
                    colWidths=[leftIndent,None],
                    style=TableStyle([["TOPPADDING",[0,0],[-1,-1],0],
                           ["LEFTPADDING",[0,0],[-1,-1],0],
                           ["RIGHTPADDING",[0,0],[-1,-1],rightIndent],
                           ["BOTTOMPADDING",[0,0],[-1,-1],0],
                    ])), Spacer(0,spaceAfter)]
            else:
                node.elements=[Spacer(0,spaceBefore),DelayedTable(data,
                    colWidths=[leftIndent,None],
                    style=TableStyle([["TOPPADDING",[0,0],[-1,-1],0],
                           ["LEFTPADDING",[0,0],[-1,-1],0],
                           ["RIGHTPADDING",[0,0],[-1,-1],rightIndent],
                           ["BOTTOMPADDING",[0,0],[-1,-1],0],
                    ])), Spacer(0,spaceAfter)]

        elif isinstance(node, docutils.nodes.attribution):
            node.elements = [
                Paragraph(client.gather_pdftext(node),
                          client.styles['attribution'])]

        elif isinstance(node, docutils.nodes.comment):
            # Class that generates no output
            node.elements = []

        elif isinstance(node, docutils.nodes.line_block):
            if isinstance(node.parent,docutils.nodes.line_block):
                qstyle = copy(style)
                qstyle.leftIndent += client.styles.adjustUnits("1.5em")
            else:
                qstyle = copy(client.styles['lineblock'])
            # Fix Issue 225: no space betwen line in a lineblock, but keep
            # space before the lineblock itself
            qstyle.spaceBefore=0
            node.elements = [Spacer(0,client.styles['lineblock'].spaceBefore)]+client.gather_elements(node, style=qstyle)

        elif isinstance(node, docutils.nodes.line):
            # All elements in one line
            node.elements = [Paragraph(client.gather_pdftext(node),
                                       style=style)]

        elif isinstance(node, (docutils.nodes.literal_block,
                               docutils.nodes.doctest_block)):
            node.elements = [client.PreformattedFit(
                client.gather_pdftext(node, replaceEnt = True),
                                client.styles['code'])]

        elif isinstance(node, docutils.nodes.image):
            # FIXME: handle class,target,alt, check align
            imgname = os.path.join(client.basedir,str(node.get("uri")))
            if not os.path.exists(imgname):
                log.error("Missing image file: %s [%s]",imgname, nodeid(node))
                imgname = os.path.join(client.img_dir, 'image-missing.png')
                w, h, kind = 1*cm, 1*cm, 'direct'
            else:
                w, h, kind = client.size_for_image_node(node)
            extension = imgname.split('.')[-1].lower()
            if extension in (
                    'ai', 'ccx', 'cdr', 'cgm', 'cmx', 'fig',
                    'sk1', 'sk', 'svg', 'xml', 'wmf'):
                node.elements = [SVGImage(filename=imgname,
                                          height=h,
                                          width=w,
                                          kind=kind)]
            elif extension == 'pdf':
                try:
                    #import rlextra.pageCatcher.pageCatcher as pageCatcher
                    raise Exception("Broken")
                    node.elements = \
                        [pageCatcher.PDFImageFlowable(imgname, w, h)]
                except:
                    log.warning("Proper PDF images require "\
                        "pageCatcher (but doesn't work yet) [%s]",
                        nodeid(node))
                    if HAS_MAGICK:
                        # w,h are in pixels. I need to set the density
                        # of the image to  the right dpi so this
                        # looks decent
                        img = PMImage()
                        img.density("%s"%client.styles.def_dpi)
                        img.read(imgname)
                        _, tmpname = tempfile.mkstemp(suffix='.png')
                        img.write(tmpname)
                        client.to_unlink.append(tmpname)
                        node.elements = [MyImage(filename=tmpname,
                                                 height=h,
                                                 width=w,
                                                 kind=kind)]
                    else:
                        log.warning("Minimal PDF image support "\
                            "requires PythonMagick [%s]", nodeid(node))
                        imgname = os.path.join(client.img_dir, 'image-missing.png')
                        w, h, kind = 1*cm, 1*cm, 'direct'
            elif not HAS_PIL and HAS_MAGICK and extension != 'jpg':
                # Need to convert to JPG via PythonMagick
                img = PMImage(imgname)
                _, tmpname = tempfile.mkstemp(suffix='.jpg')
                img.write(tmpname)
                client.to_unlink.append(tmpname)
                node.elements = [MyImage(filename=tmpname, height=h, width=w,
                            kind=kind)]

            elif HAS_PIL or extension == 'jpg':
                node.elements = [MyImage(filename=imgname, height=h, width=w,
                    kind=kind)]
            else:
                # No way to make this work
                log.error('To use a %s image you need PIL installed [%s]',extension, nodeid(node))
                node.elements = []
            if node.elements:
                i = node.elements[0]
                alignment = node.get('align', 'CENTER').upper()
                if alignment in ('LEFT', 'CENTER', 'RIGHT'):
                    i.hAlign = alignment
            # Image flowables don't support valign (makes no sense for them?)
            # elif alignment in ('TOP','MIDDLE','BOTTOM'):
            #    i.vAlign = alignment

        elif isinstance(node, docutils.nodes.figure):
            sub_elems = client.gather_elements(node, style=None)
            node.elements = [BoxedContainer(sub_elems, style)]

        elif isinstance(node, docutils.nodes.caption):
            node.elements = [Paragraph(client.gather_pdftext(node),
                                       style=client.styles['figure-caption'])]

        elif isinstance(node, docutils.nodes.legend):
            node.elements = client.gather_elements(node,
                style=client.styles['figure-legend'])

        elif isinstance(node, docutils.nodes.sidebar):
            node.elements = [BoxedContainer(client.gather_elements(node,
                                                                 style=None),
                                            client.styles['sidebar'])]

        elif isinstance(node, docutils.nodes.rubric):
            # Sphinx uses a rubric as footnote container
            if HAS_SPHINX and len(node.children) == 1 \
                and node.children[0].astext() == 'Footnotes':
                    node.elements=[Separation(),]
            else:
                node.elements = [Paragraph(client.gather_pdftext(node),
                                       client.styles['rubric'])]

        elif isinstance(node, docutils.nodes.compound):
            # FIXME think if this is even implementable
            node.elements = client.gather_elements(node, style)

        elif isinstance(node, docutils.nodes.container):
            # FIXME think if this is even implementable
            node.elements = client.gather_elements(node, style)

        elif isinstance(node, docutils.nodes.substitution_definition):
            node.elements = []

        elif isinstance(node, docutils.nodes.tbody):
            rows = [client.gen_elements(n) for n in node.children]
            t = []
            for r in rows:
                if not r:
                    continue
                t.append(r)
            t_style = TableStyle(client.styles['table'].commands)
            colWidths = client.styles['table'].colWidths
            node.elements = [DelayedTable(t, style=t_style, colWidths=colWidths)]

        elif isinstance(node, (docutils.nodes.footnote,
                               docutils.nodes.citation)):
            # It seems a footnote contains a label and a series of elements
            ltext = client.gather_pdftext(node.children[0])
            if len(node['backrefs']) > 1 and client.footnote_backlinks:
                backrefs = []
                i = 1
                for r in node['backrefs']:
                    backrefs.append('<a href="#%s" color="%s">%d</a>' % (
                        r, client.styles.linkColor, i))
                    i += 1
                backrefs = '(%s)' % ', '.join(backrefs)
                if ltext not in client.targets:
                    label = Paragraph('<a name="%s"/>%s'%(ltext,
                                                      ltext + backrefs),
                                  client.styles["normal"])
                    client.targets.append(ltext)
            elif len(node['backrefs'])==1 and client.footnote_backlinks:
                if ltext not in client.targets:
                    label = Paragraph('<a name="%s"/>'\
                                  '<a href="%s" color="%s">%s</a>' % (
                                        ltext,
                                        node['backrefs'][0],
                                        client.styles.linkColor,
                                        ltext), client.styles["normal"])
                    client.targets.append(ltext)
            else:
                if ltext not in client.targets:
                    label = Paragraph('<a name="%s"/>%s' % (ltext, ltext),
                        client.styles["normal"])
                    client.targets.append(ltext)
            contents = client.gather_elements(node, style)[1:]
            if client.inline_footnotes:
                st=client.styles['endnote']
                t_style = TableStyle(st.commands)
                colWidths = client.styles['endnote'].colWidths
                node.elements = [Spacer(0, st.spaceBefore),
                                 DelayedTable([[label, contents]],
                                 style=t_style, colWidths=colWidths),
                                 Spacer(0, st.spaceAfter)]
            else:
                client.decoration['endnotes'].append([label, contents])
                node.elements = []

        elif isinstance(node, docutils.nodes.label):
            node.elements = [Paragraph(client.gather_pdftext(node), style)]
        elif isinstance(node, docutils.nodes.Text):
            node.elements = [Paragraph(client.gather_pdftext(node), style)]
        elif isinstance(node, docutils.nodes.entry):
            node.elements = client.gather_elements(node, style)

        elif isinstance(node, docutils.nodes.target):
            if 'refid' in node:
                client.pending_targets.append(node['refid'])
            node.elements = client.gather_elements(node, style)

        elif isinstance(node, docutils.nodes.reference):
            node.elements = client.gather_elements(node, style)

        elif isinstance(node, docutils.nodes.raw):
            # Not really raw, but what the heck
            if node.get('format','NONE').lower()=='pdf':
                node.elements = parseRaw(str(node.astext()))
            else:
                node.elements = []

        elif isinstance(node, docutils.nodes.citation):
            node.elements = []

        elif isinstance(node, Aanode):
            style_options = {
                'font': client.styles['aafigure'].fontName,
                }
            node.elements = [node.gen_flowable(style_options)]

        # custom SPHINX nodes.
        # FIXME: make sure they are all here, and keep them all together
        elif HAS_SPHINX and isinstance(node, sphinx.addnodes.centered):
            node.elements=[Paragraph(client.gather_pdftext(node),
                client.styles['centered'])]
        elif HAS_SPHINX and isinstance(node, sphinx.addnodes.desc):

            st=client.styles[node['desctype']]
            if st==client.styles['normal']:
                st=copy(client.styles['desc'])
                st.spaceBefore=0

            pre=[Spacer(0,client.styles['desc'].spaceBefore)]
            node.elements = pre+\
                client.gather_elements(node, st)

        elif HAS_SPHINX and isinstance(node, sphinx.addnodes.desc_signature):
            # Need to add ids as targets, found this when using one of the
            # django docs extensions
            targets=[i.replace(' ','') for i in node['ids']]
            pre=''
            for i in targets:
                if i not in client.targets:
                    pre+='<a name="%s" />'% i
                    client.targets.append(i)
            node.elements = [Paragraph(pre+client.gather_pdftext(node),style)]
        elif HAS_SPHINX and isinstance(node, sphinx.addnodes.desc_content):
            node.elements = [MyIndenter(left=10)] +\
                client.gather_elements(node, client.styles["definition"]) +\
                [MyIndenter(left=-10)]

        # These are here because sphinx.addnodes.desc inherits Admonition
        elif isinstance(node, (docutils.nodes.attention,
                docutils.nodes.caution, docutils.nodes.danger,
                docutils.nodes.error, docutils.nodes.hint,
                docutils.nodes.important, docutils.nodes.note,
                docutils.nodes.tip, docutils.nodes.warning,
                docutils.nodes.Admonition)):
            if node.children and isinstance(node.children[0], docutils.nodes.title):
                title=[]
            else:
                title= [Paragraph(node.tagname.title(),
                    style=client.styles['%s-heading'%node.tagname])]
            rows=title + client.gather_elements(node, style=style)
            st=client.styles[node.tagname]
            if 'commands' in dir(st):
                t_style = TableStyle(st.commands)
            else:
                t_style = TableStyle()
            t_style.add("ROWBACKGROUNDS", [0, 0], [-1, -1],[st.backColor])
            t_style.add("BOX", [ 0, 0 ], [ -1, -1 ], st.borderWidth , st.borderColor)

            if client.splittables:
                node.elements = [Spacer(0,st.spaceBefore),
                                 SplitTable([['',rows]],
                                 style=t_style,
                                 colWidths=[0,None],
                                 padding=st.borderPadding),
                                 Spacer(0,st.spaceAfter)]
            else:
                padding, p1, p2, p3, p4=tablepadding(padding=st.borderPadding)
                t_style.add(*p1)
                t_style.add(*p2)
                t_style.add(*p3)
                t_style.add(*p4)
                node.elements = [Spacer(0,st.spaceBefore),
                                 DelayedTable([['',rows]],
                                 style=t_style,
                                 colWidths=[0,None]),
                                 Spacer(0,st.spaceAfter)]



        else:
            # With sphinx you will have hundreds of these
            #if not HAS_SPHINX:
            cln=str(node.__class__)
            if not cln in unkn_elem:
                unkn_elem.add(cln)
                log.error("Unkn. node (gen_elements): %s [%s]",
                str(node.__class__), nodeid(node))
                    # Why fail? Just log it and do our best.
            node.elements = client.gather_elements(node, style)

        # Make all the sidebar cruft unreachable
        #if style.__dict__.get('float','None').lower() !='none':
            #node.elements=[Sidebar(node.elements,style)]
        #elif 'width' in style.__dict__:
        if 'width' in style.__dict__:
            node.elements = [BoundByWidth(style.width,
                node.elements, style, mode="shrink")]

        if node.line and client.debugLinesPdf:
            node.elements.insert(0,TocEntry(client.depth-1,'LINE-%s'%node.line))
            
        return node.elements
