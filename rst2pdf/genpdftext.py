# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

import os
from xml.sax.saxutils import escape
from utils import NodeHandler
from log import log, nodeid
from math_directive import math_node
import docutils.nodes
from smartypants import smartyPants
from urlparse import urljoin, urlparse
from reportlab.lib.units import cm
from math_flowable import Math


class GenPdfText(NodeHandler):
    _baseclass = None

    # Begin overridable attributes and methods for gen_pdftext

    pre = ''
    post = ''

    def get_pre_post(self, client, node, replaceEnt):
        return self.pre, self.post

    def get_text(self, client, node, replaceEnt):
        return client.gather_pdftext(node)

    def apply_smartypants(self, text, smarty, node):
        # Try to be clever about when to use smartypants
        if node.__class__ in (docutils.nodes.paragraph,
                docutils.nodes.block_quote, docutils.nodes.title):
            return smartyPants(text, smarty)
        return text

    # End overridable attributes and methods for gen_pdftext

    @classmethod
    def dispatch(cls, client, node, replaceEnt=True):
        self = cls.findsubclass(node)
        pre, post = self.get_pre_post(client, node, replaceEnt)
        text = self.get_text(client, node, replaceEnt)
        text = pre + text + post

        try:
            log.debug("self.gen_pdftext: %s" % text)
        except UnicodeDecodeError:
            pass

        text = self.apply_smartypants(text, client.smarty, node)
        node.pdftext = text
        return text


class HandleNotDefinedYet(GenPdfText, object):
    def __init__(self):
        self.unkn_text = set()
        GenPdfText.default_dispatch = self

    def get_text(self, client, node, replaceEnt):
        cln=str(node.__class__)
        if not cln in self.unkn_text:
            self.unkn_text.add(cln)
            log.warning("Unkn. node (self.gen_pdftext): %s [%s]",
                node.__class__, nodeid(node))
            try:
                log.debug(node)
            except (UnicodeDecodeError, UnicodeEncodeError):
                log.debug(repr(node))
        return GenPdfText.get_text(self, client, node, replaceEnt)

class FontHandler(GenPdfText):
    def get_pre_post(self, client, node, replaceEnt):
        return self.get_font_prefix(client, node, replaceEnt), '</font>'

    def get_font_prefix(self, client, node, replaceEnt):
        return client.styleToFont(self.fontstyle)

class HandlePara(GenPdfText, docutils.nodes.paragraph,
                      docutils.nodes.title, docutils.nodes.subtitle):
    def get_pre_post(self, client, node, replaceEnt):
        pre=''
        targets=set(node.get('ids',[])+client.pending_targets)
        client.pending_targets=[]
        for _id in targets:
            if _id not in client.targets:
                pre+='<a name="%s"/>'%(_id)
                client.targets.append(_id)
        return pre, '\n'

class HandleText(GenPdfText, docutils.nodes.Text):
    def get_text(self, client, node, replaceEnt):
        text = node.astext()
        if replaceEnt:
            text = escape(text)
        return text

class HandleStrong(GenPdfText, docutils.nodes.strong):
    pre = "<b>"
    post = "</b>"

class HandleEmphasis(GenPdfText, docutils.nodes.emphasis):
    pre = "<i>"
    post = "</i>"

class HandleLiteral(GenPdfText, docutils.nodes.literal):
    def get_pre_post(self, client, node, replaceEnt):
        pre = '<font face="%s">' % client.styles['literal'].fontName
        post = "</font>"
        if not client.styles['literal'].hyphenation:
            pre = '<nobr>' + pre
            post += '</nobr>'
        return pre, post

class HandleSuper(GenPdfText, docutils.nodes.superscript):
    pre = '<super>'
    post = "</super>"

class HandleSub(GenPdfText, docutils.nodes.subscript):
    pre = '<sub>'
    post = "</sub>"

class HandleTitleReference(FontHandler, docutils.nodes.title_reference):
    fontstyle = 'title_reference'

class HandleReference(GenPdfText, docutils.nodes.reference):
    def get_pre_post(self, client, node, replaceEnt):
        pre, post = '', ''
        uri = node.get('refuri')
        if uri:
            if client.baseurl: # Need to join the uri with the base url
                uri = urljoin(client.baseurl, uri)

            if urlparse(uri)[0] and client.inlinelinks:
                # external inline reference
                post = u' (%s)' % uri
            else:
                # A plain old link
                pre += u'<a href="%s" color="%s">' %\
                    (uri, client.styles.linkColor)
                post = '</a>' + post
        else:
            uri = node.get('refid')
            if uri:
                pre += u'<a href="#%s" color="%s">' %\
                    (uri, client.styles.linkColor)
                post = '</a>' + post
        return pre, post

class HandleOptions(HandleText, docutils.nodes.option_string, docutils.nodes.option_argument):
    pass

class HandleHeaderFooter(HandleText, docutils.nodes.header, docutils.nodes.footer):
    pass

class HandleSysMessage(HandleText, docutils.nodes.system_message, docutils.nodes.problematic):
    pre = '<font color="red">'
    post = "</font>"

class HandleGenerated(HandleText, docutils.nodes.generated):
    pass

class HandleImage(GenPdfText, docutils.nodes.image):
    def get_text(self, client, node, replaceEnt):
        # First see if the image file exists, or else,
        # use image-missing.png
        uri=node.get('uri')
        if not os.path.exists(uri):
            log.error("Missing image file: %s [%s]", uri, nodeid(node))
            uri=os.path.join(client.img_dir, 'image-missing.png')
            w, h = 1*cm, 1*cm
        else:
            w, h, kind = client.size_for_image_node(node)
        alignment=node.get('align', 'CENTER').lower()
        if alignment in ('top', 'middle', 'bottom'):
            align='valign="%s"'%alignment
        else:
            align=''

        return '<img src="%s" width="%f" height="%f" %s/>'%\
            (uri, w, h, align)

class HandleMath(GenPdfText, math_node):
    def get_text(self, client, node, replaceEnt):
        mf = Math(node.math_data)
        w, h = mf.wrap(0, 0)
        descent = mf.descent()
        img = mf.genImage()
        client.to_unlink.append(img)
        return '<img src="%s" width=%f height=%f valign=%f/>' % (
            img, w, h, -descent)

class HandleFootRef(GenPdfText, docutils.nodes.footnote_reference):
    def get_text(self, client, node, replaceEnt):
        # TODO: when used in Sphinx, all footnotes are autonumbered
        anchors=''
        for i in node['ids']:
            if i not in client.targets:
                anchors+='<a name="%s"/>' % i
                client.targets.append(i)
        return u'%s<super><a href="%s" color="%s">%s</a></super>'%\
            (anchors, '#' + node.astext(),
                client.styles.linkColor, node.astext())

class HandleCiteRef(GenPdfText, docutils.nodes.citation_reference):
    def get_text(self, client, node, replaceEnt):
        anchors=''
        for i in node['ids']:
            if i not in client.targets:
                anchors +='<a name="%s"/>' % i
                client.targets.append(i)
        return u'%s[<a href="%s" color="%s">%s</a>]'%\
            (anchors, '#' + node.astext(),
                client.styles.linkColor, node.astext())

class HandleTarget(GenPdfText, docutils.nodes.target):
    def get_text(self, client, node, replaceEnt):
        text = client.gather_pdftext(node)
        if replaceEnt:
            text = escape(text)
        return text

    def get_pre_post(self, client, node, replaceEnt):
        pre = ''
        if node['ids'][0] not in client.targets:
            pre = u'<a name="%s"/>' % node['ids'][0]
            client.targets.append(node['ids'][0])
        return pre, ''

class HandleInline(GenPdfText, docutils.nodes.inline):
    def get_pre_post(self, client, node, replaceEnt):
        ftag = client.styleToFont(node['classes'][0])
        if ftag:
            return ftag, '</font>'
        return '', ''

class HandleLiteralBlock(GenPdfText, docutils.nodes.literal_block):
    pass


def add_sphinx():
    import sphinx

    class HandleSphinxDefaults(GenPdfText,
                 sphinx.addnodes.desc_signature,
                 sphinx.addnodes.module,
                 sphinx.addnodes.pending_xref):
        pass

    class SphinxListHandler(GenPdfText):
        def get_text(self, client, node, replaceEnt):
            t = client.gather_pdftext(node)
            while t and t[0] in ', ':
                t=t[1:]
            return t

    class HandleSphinxDescAddname(FontHandler,  sphinx.addnodes.desc_addname):
        fontstyle = "descclassname"

    class HandleSphinxDescName(FontHandler, sphinx.addnodes.desc_name):
        fontstyle = "descname"

    class HandleSphinxDescReturn(FontHandler, sphinx.addnodes.desc_returns):
        def get_font_prefix(self, client, node, replaceEnt):
            return ' &rarr; ' + client.styleToFont("returns")

    class HandleSphinxDescType(FontHandler, sphinx.addnodes.desc_type):
        fontstyle = "desctype"

    class HandleSphinxDescParamList(SphinxListHandler, sphinx.addnodes.desc_parameterlist):
        pre=' ('
        post=')'

    class HandleSphinxDescParam(FontHandler, sphinx.addnodes.desc_parameter):
        fontstyle = "descparameter"
        def get_pre_post(self, client, node, replaceEnt):
            pre, post = FontHandler.get_pre_post(self, client, node, replaceEnt)
            if node.hasattr('noemph'):
                pre = ', ' + pre
            else:
                pre = ', <i>' + pre
                post += '</i>'
            return pre, post

    class HandleSphinxDescOpt(SphinxListHandler, FontHandler, sphinx.addnodes.desc_optional):
        fontstyle = "optional"
        def get_pre_post(self, client, node, replaceEnt):
            prepost = FontHandler.get_pre_post(self, client, node, replaceEnt)
            return '%s[%s, ' % prepost, '%s]%s' % prepost

    class HandleDescAnnotation(HandleEmphasis, sphinx.addnodes.desc_annotation):
        pass

dispatch = GenPdfText.dispatch
