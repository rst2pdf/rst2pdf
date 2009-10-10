# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$
import unittest
import cStringIO

import reportlab
from docutils.core import publish_doctree
from pyPdf import PdfFileReader

import rst2pdf
from utils import *

import pdb
#import pdb; pdb.set_trace()

def input_file_path(file):
    return join(PREFIX, 'input', file)

class FullGenerationTests(unittest.TestCase):
    """ broken since createPdf is no longer a function
    """
    def test_bullet_chars_full(self):
        self.output=cStringIO.StringIO()
        input_file = input_file_path('test_bullet_chars.txt')
        input=open(input_file,'r').read()
        createPdf(text=input, output=self.output, styleSheet=None)
        self.output.seek(0)
        result = PdfFileReader(self.output)
        text_result = result.getPage(0).extractText()
        self.assertEqual(text_result, u'\nTest\nItem 1\nItem 2\n')


class GenerationTests(rst2pdfTests):


    def test_transition(self):
        input="""
Transitions
-----------

Here's a transition:

---------

It divides the section.
"""
        doctree=publish_doctree(input)
        elements=self.converter.gen_elements(doctree,0)
        self.assertEqual(len(elements), 5)
        assert(isinstance(elements[3],rst2pdf.flowables.Separation))

    def test_strong(self):
        input="""
**strong**"""
        doctree=publish_doctree(input)
        elements=self.converter.gen_elements(doctree,0)
        self.assertEqual(len(elements), 1)
        para = elements[0]
        self.assertEqual(para.text, '<b>strong</b>')
        parafrag = para.frags[0]
        self.assertEqual(parafrag.bold, 1)

    def test_emphasis(self):
        input="""
*emphasis*"""
        doctree=publish_doctree(input)
        elements=self.converter.gen_elements(doctree,0)
        self.assertEqual(len(elements), 1)
        para = elements[0]
        self.assertEqual(para.text, '<i>emphasis</i>')
        parafrag = para.frags[0]
        self.assertEqual(parafrag.italic, 1)
        # pdb.set_trace()

    def test_raw_pagebreak(self):
        input="""
One page

.. raw:: pdf

   PageBreak

Another page.
"""
        doctree=publish_doctree(input)
        elements=self.converter.gen_elements(doctree,0)
        self.assertEqual(len(elements), 3)
        pagebreak = elements[1]
        self.assertEqual(pagebreak.__class__, rst2pdf.flowables.MyPageBreak)
        #pdb.set_trace()

    def test_raw_spacer(self):
        input="""
A paragraph

.. raw:: pdf

    Spacer 0,200

And another paragraph.

"""
        doctree=publish_doctree(input)
        elements=self.converter.gen_elements(doctree,0)
        self.assertEqual(len(elements), 3)
        spacer = elements[1]
        self.assertEqual(spacer.__class__, reportlab.platypus.flowables.Spacer)
        #pdb.set_trace()

    def test_bullets(self):
        input="""
 Test
======

- Item 1
- Item 2
"""
        doctree=publish_doctree(input)
        elements=self.converter.gen_elements(doctree,0)
        self.assertEqual(len(elements), 4)
        self.assertEqual(elements[1].text, 'Test')
        self.assertEqual(elements[2].text, 'Item 1')
        self.assertEqual(elements[2].bulletText, u'\u2022')
        self.assertEqual(elements[3].text, 'Item 2')
        self.assertEqual(elements[3].bulletText, u'\u2022')

    def test_sidebar(self):
        input="""
.. sidebar:: The Sidebar

   This is a real sidebar, declared with the sidebar directive.

Quisque dignissim. Duis in velit vel augue rhoncus pretium. Duis non nisl in lorem placerat rutrum.
"""
        doctree=publish_doctree(input)
        elements=self.converter.gen_elements(doctree,0)
        self.assertEqual(len(elements), 2)
        sidebar = elements[0]
        self.assertEqual(sidebar.__class__, rst2pdf.flowables.Sidebar)
        #pdb.set_trace()


def test_suite():
    suite = unittest.makeSuite(GenerationTests)
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
