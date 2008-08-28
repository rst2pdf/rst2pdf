# -*- coding: utf-8 -*-
import unittest
from pyPdf import PdfFileReader
import cStringIO
from rst2pdf.createpdf import createPdf

from os.path import join, abspath, dirname, basename
PREFIX = abspath(dirname(__file__))

def input_file_path(file):
    return join(PREFIX, 'input', file)

class GenerationTests(unittest.TestCase):

    def setUp(self):
        self.output=cStringIO.StringIO()
        
        
    def tearDown(self):
        pass
        
    def test_bullet_chars(self):
        input_file = input_file_path('test_bullet_chars.txt')
        input=open(input_file,'r').read()
        createPdf(text=input, output=self.output, styleSheet=None)
        self.output.seek(0)
        result = PdfFileReader(self.output)
        text_result = result.getPage(0).extractText()
        self.assertEqual(text_result, u'\nTest\nItem 1\nItem 2\n')
        
def test_suite():
    return unittest.makeSuite(GenerationTests)
    
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
