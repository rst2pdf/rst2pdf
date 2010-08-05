# -*- coding: utf-8 -*-
import rst2pdf.genelements as genelements
from rst2pdf.flowables import Heading
import docutils
import reportlab

class FancyTitle(genelements.HandleParagraph, docutils.nodes.title):
    def gather_elements(self, client, node, style):
        print 'XXX'
        # Special cases: (Not sure this is right ;-)
        if isinstance(node.parent, docutils.nodes.document):
            #node.elements = [Paragraph(client.gen_pdftext(node),
                                        #client.styles['title'])]
            # The visible output is now done by the cover template
            node.elements = []
            client.doc_title = node.rawsource
            client.doc_title_clean = node.astext().strip()
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
        return node.elements
