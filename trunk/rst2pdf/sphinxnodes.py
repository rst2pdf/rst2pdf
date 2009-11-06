# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

from copy import copy
from genelements import GenElements

from log import nodeid
from flowables import  Spacer, MyIndenter, Reference

from opt_imports import Paragraph, sphinx
from genpdftext import GenPdfText, FontHandler, HandleEmphasis

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


class HandleSphinxDefaults(GenElements, sphinx.addnodes.glossary,
                                        sphinx.addnodes.start_of_file,
                                        sphinx.addnodes.compact_paragraph):
    pass

class HandleSphinxIndex(GenElements, sphinx.addnodes.index):
    def gather_elements(self, client, node, style):
        try:
            client.pending_targets.append(node['entries'][0][2])
        except IndexError:
            if node['entries']:
                log.error("Can't process index entry: %s [%s]",
                    node['entries'], nodeid(node))
        return []

class HandleSphinxModule(GenElements, sphinx.addnodes.module):
    def gather_elements(self, client, node, style):
        return [Reference('module-'+node['modname'])]

# custom SPHINX nodes.
# FIXME: make sure they are all here, and keep them all together

class HandleSphinxCentered(GenElements, sphinx.addnodes.centered):
    def gather_elements(self, client, node, style):
        return [Paragraph(client.gather_pdftext(node),
                client.styles['centered'])]

class HandleSphinxDesc(GenElements, sphinx.addnodes.desc):
    def gather_elements(self, client, node, style):
        st=client.styles[node['desctype']]
        if st==client.styles['normal']:
            st=copy(client.styles['desc'])
            st.spaceBefore=0
        pre=[Spacer(0,client.styles['desc'].spaceBefore)]
        return pre + client.gather_elements(node, st)

class HandleSphinxDescSignature(GenElements, sphinx.addnodes.desc_signature):
    def gather_elements(self, client, node, style):
        # Need to add ids as targets, found this when using one of the
        # django docs extensions
        targets=[i.replace(' ','') for i in node['ids']]
        pre=''
        for i in targets:
            if i not in client.targets:
                pre+='<a name="%s" />'% i
                client.targets.append(i)
        return [Paragraph(pre+client.gather_pdftext(node),style)]

class HandleSphinxDescContent(GenElements, sphinx.addnodes.desc_content):
    def gather_elements(self, client, node, style):
        return [MyIndenter(left=10)] +\
                client.gather_elements(node, client.styles["definition"]) +\
                [MyIndenter(left=-10)]
