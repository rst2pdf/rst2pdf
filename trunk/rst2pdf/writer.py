# -*- coding: utf-8 -*-

from rst2pdf import createpdf
from docutils import writers
from StringIO import StringIO
import sys
from tempfile import mkstemp
import codecs

class PdfWriter(writers.Writer):

    def __init__(self, builder):
        writers.Writer.__init__(self)
        self.builder = builder
        self.output = u''

    supported = ('pdf')
    """Formats this writer supports."""

    config_section = 'pdf writer'
    config_section_dependencies = ('writers',)

    """Final translated form of `document`."""

    def translate(self):
        sio=StringIO('')
        createpdf.RstToPdf().createPdf(doctree=self.document,output=sio,compressed=False)
        self.output=unicode(sio.getvalue(),'utf-8','ignore')

    def supports(self, format):
        """This writer supports all format-specific elements."""
        return 1
