# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

'''
This module contains sphinx-specific node handlers for GenElements
and GenPdfText.  An import of this module will fail if an import
of sphinx would fail.

This module creates separate sphinx-specific dispatch dictionaries,
which are kept separate from the regular ones.

At the end of the module, the separate dispatch dictionaries and
the regular ones are combined into instantiated dispatch objects
for pdftext and elements.
'''

from copy import copy
from genelements import GenElements

from log import nodeid
from flowables import  Spacer, MyIndenter, Reference

from opt_imports import Paragraph, sphinx
from genpdftext import GenPdfText, FontHandler, HandleEmphasis


################## GenPdfText subclasses ###################

class SphinxText(GenPdfText):
    sphinxmode = True
    dispatchdict = {}

class SphinxFont(SphinxText, FontHandler):
    pass

class HandleSphinxDefaults(SphinxText,
                sphinx.addnodes.desc_signature,
                sphinx.addnodes.module,
                sphinx.addnodes.pending_xref):
    pass

class SphinxListHandler(SphinxText):
    def get_text(self, client, node, replaceEnt):
        t = client.gather_pdftext(node)
        while t and t[0] in ', ':
            t=t[1:]
        return t

class HandleSphinxDescAddname(SphinxFont,  sphinx.addnodes.desc_addname):
    fontstyle = "descclassname"

class HandleSphinxDescName(SphinxFont, sphinx.addnodes.desc_name):
    fontstyle = "descname"

class HandleSphinxDescReturn(SphinxFont, sphinx.addnodes.desc_returns):
    def get_font_prefix(self, client, node, replaceEnt):
        return ' &rarr; ' + client.styleToFont("returns")

class HandleSphinxDescType(SphinxFont, sphinx.addnodes.desc_type):
    fontstyle = "desctype"

class HandleSphinxDescParamList(SphinxListHandler, sphinx.addnodes.desc_parameterlist):
    pre=' ('
    post=')'

class HandleSphinxDescParam(SphinxFont, sphinx.addnodes.desc_parameter):
    fontstyle = "descparameter"
    def get_pre_post(self, client, node, replaceEnt):
        pre, post = FontHandler.get_pre_post(self, client, node, replaceEnt)
        if node.hasattr('noemph'):
            pre = ', ' + pre
        else:
            pre = ', <i>' + pre
            post += '</i>'
        return pre, post

class HandleSphinxDescOpt(SphinxListHandler, SphinxFont, sphinx.addnodes.desc_optional):
    fontstyle = "optional"
    def get_pre_post(self, client, node, replaceEnt):
        prepost = FontHandler.get_pre_post(self, client, node, replaceEnt)
        return '%s[%s, ' % prepost, '%s]%s' % prepost

class HandleDescAnnotation(SphinxText, HandleEmphasis, sphinx.addnodes.desc_annotation):
    pass

################## GenElements subclasses ###################

class SphinxElements(GenElements):
    sphinxmode = True
    dispatchdict = {}

class HandleSphinxDefaults(SphinxElements, sphinx.addnodes.glossary,
                                        sphinx.addnodes.start_of_file,
                                        sphinx.addnodes.compact_paragraph):
    pass

class HandleSphinxIndex(SphinxElements, sphinx.addnodes.index):
    def gather_elements(self, client, node, style):
        try:
            client.pending_targets.append(node['entries'][0][2])
        except IndexError:
            if node['entries']:
                log.error("Can't process index entry: %s [%s]",
                    node['entries'], nodeid(node))
        return []

class HandleSphinxModule(SphinxElements, sphinx.addnodes.module):
    def gather_elements(self, client, node, style):
        return [Reference('module-'+node['modname'])]

# custom SPHINX nodes.
# FIXME: make sure they are all here, and keep them all together

class HandleSphinxCentered(SphinxElements, sphinx.addnodes.centered):
    def gather_elements(self, client, node, style):
        return [Paragraph(client.gather_pdftext(node),
                client.styles['centered'])]

class HandleSphinxDesc(SphinxElements, sphinx.addnodes.desc):
    def gather_elements(self, client, node, style):
        st=client.styles[node['desctype']]
        if st==client.styles['normal']:
            st=copy(client.styles['desc'])
            st.spaceBefore=0
        pre=[Spacer(0,client.styles['desc'].spaceBefore)]
        return pre + client.gather_elements(node, st)

class HandleSphinxDescSignature(SphinxElements, sphinx.addnodes.desc_signature):
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

class HandleSphinxDescContent(SphinxElements, sphinx.addnodes.desc_content):
    def gather_elements(self, client, node, style):
        return [MyIndenter(left=10)] +\
                client.gather_elements(node, client.styles["definition"]) +\
                [MyIndenter(left=-10)]

################## Housekeeping ###################


def builddict():
    ''' This is where the magic happens.  Make a copy of the elements
        in the non-sphinx dispatch dictionary, setting sphinxmode on
        every element, and then overwrite that dictionary with any
        sphinx-specific handlers.
    '''
    for cls in (SphinxText, SphinxElements):
        self = cls()
        mydict = {}
        for key, value in self._baseclass.dispatchdict.iteritems():
            value = copy(value)
            value.sphinxmode = True
            mydict[key] = value
        mydict.update(self.dispatchdict)
        self.dispatchdict = mydict
        yield self

textdispatch, elemdispatch = builddict()
textdispatch, elemdispatch = textdispatch.textdispatch, elemdispatch.elemdispatch
