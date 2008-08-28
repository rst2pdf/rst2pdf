# -*- coding: utf-8 -*-
from unittest import TestCase, makeSuite
from pyPdf import PdfFileReader
import cStringIO
import rst2pdf
from rst2pdf.createpdf import RstToPdf

import docutils.core

from os.path import join, abspath, dirname, basename
PREFIX = abspath(dirname(__file__))

import pdb

def input_file_path(file):
    return join(PREFIX, 'input', file)

class rst2pdfTests(TestCase):

    def setUp(self):
        self.converter=RstToPdf()
    
class FullGenerationTests(TestCase):
    def test_bullet_chars_full(self):
        self.output=cStringIO.StringIO()
        input_file = input_file_path('test_bullet_chars.txt')
        input=open(input_file,'r').read()
        createPdf(text=input, output=self.output, styleSheet=None)
        self.output.seek(0)
        result = PdfFileReader(self.output)
        text_result = result.getPage(0).extractText()
        self.assertEqual(text_result, u'\nTest\nItem 1\nItem 2\n')

    
class IncludeTests(rst2pdfTests):
    def test_wrong_file(self):
        input="""
This one gives a warning, non existent file:

.. code-block:: python
   :include: xyzzy.py
"""
        doctree=docutils.core.publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.astext(), u'\n')
        
    def test_missing_file(self):
        input="""
This one gives a warning, missing file:

.. code-block:: python
   :include:
"""
        doctree=docutils.core.publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'system_message')
        self.assertEqual(include.children[1].tagname, 'literal_block')
        self.assertEqual(include.children[1].astext(), u'.. code-block:: python\n   :include:')

    def test_existing_file(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
""" % __file__
        doctree=docutils.core.publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.children[0].astext(), u'# -*- coding: utf-8 -*-')

    def test_existing_file_start_at(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
   :start-at: def input_file_path(file):
""" % __file__
        doctree=docutils.core.publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.astext().split('\n')[0], u'def input_file_path(file):')
        self.assertEqual(include.astext().split('\n')[-2:][0], u"    unittest.main(defaultTest='test_suite')")
        
    def test_existing_file_end_at(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
   :end-at: def input_file_path(file):
""" % __file__
        doctree=docutils.core.publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.children[0].astext(), u'# -*- coding: utf-8 -*-')
        self.assertEqual(include.astext().split('\n')[-2:][0], u'def input_file_path(file):')
        
    def test_existing_file_start_at_end_at(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
   :start-at: def input_file_path(file):
   :end-at: return join(PREFIX, 'input', file)
""" % __file__
        doctree=docutils.core.publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.astext().split('\n')[0], u'def input_file_path(file):')
        self.assertEqual(include.astext().split('\n')[-2:][0], u"    return join(PREFIX, 'input', file)")
        
class GenerationTests(rst2pdfTests):

    def test_bullet_chars(self):
        input_file = input_file_path('test_bullet_chars.txt')
        input=open(input_file,'r').read()
        doctree=docutils.core.publish_doctree(input)
        elements=self.converter.gen_elements(doctree,0)
        self.assertEqual(len(elements), 4)
        self.assertEqual(elements[1].text, 'Test')
        self.assertEqual(elements[2]._cellvalues[0][0][0].text, 'Item 1')
        self.assertEqual(elements[2]._cellvalues[0][0][0].bulletText, u'\u2022')
        self.assertEqual(elements[3]._cellvalues[0][0][0].text, 'Item 2')
        self.assertEqual(elements[3]._cellvalues[0][0][0].bulletText, u'\u2022')
        #pdb.set_trace()
        
def test_suite():
    suite = makeSuite(GenerationTests)
    suite.addTest(makeSuite(IncludeTests))
    return suite
    
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')