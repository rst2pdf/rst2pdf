# -*- coding: utf-8 -*-
import unittest
from pyPdf import PdfFileReader
import cStringIO
import rst2pdf
from rst2pdf.createpdf import createPdf, gen_elements
from rst2pdf import styles as sty

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
        defSsheet= join(rst2pdf.__path__[0], 'styles.json')
        self.styles=sty.getStyleSheet(defSsheet)
        
    def tearDown(self):
        pass
        
        
    def test_bullet_chars(self):
        input_file = input_file_path('test_bullet_chars.txt')
        input=open(input_file,'r').read()
        doctree=docutils.core.publish_doctree(input)
        elements=gen_elements(doctree,0, style=self.styles)
        pdb.set_trace()
        
def test_suite():
    return unittest.makeSuite(GenerationTests)
    
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
