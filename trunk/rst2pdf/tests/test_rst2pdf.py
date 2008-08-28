# -*- coding: utf-8 -*-
import unittest
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

class FullGenerationTests(unittest.TestCase):
    def test_bullet_chars_full(self):
        self.output=cStringIO.StringIO()
        input_file = input_file_path('test_bullet_chars.txt')
        input=open(input_file,'r').read()
        createPdf(text=input, output=self.output, styleSheet=None)
        self.output.seek(0)
        result = PdfFileReader(self.output)
        text_result = result.getPage(0).extractText()
        self.assertEqual(text_result, u'\nTest\nItem 1\nItem 2\n')

    
class GenerationTests(unittest.TestCase):

    def setUp(self):
        self.converter=RstToPdf()
        
    def tearDown(self):
        pass
        
        
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
    return unittest.makeSuite(GenerationTests)
    
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
