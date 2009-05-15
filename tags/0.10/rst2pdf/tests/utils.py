# -*- coding: utf-8 -*-
#$HeadURL: https://rst2pdf.googlecode.com/svn/trunk/rst2pdf/tests/test_rst2pdf.py $
#$LastChangedDate: 2008-08-29 16:09:08 +0200 (Fri, 29 Aug 2008) $
#$LastChangedRevision: 160 $

from unittest import TestCase
from os.path import join, abspath, dirname, basename
PREFIX = abspath(dirname(__file__))

from rst2pdf.createpdf import RstToPdf

def input_file_path(file):
    return join(PREFIX, 'input', file)

class rst2pdfTests(TestCase):

    def setUp(self):
        self.converter=RstToPdf()
