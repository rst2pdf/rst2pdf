"""
Simple pdf Writer, writes a PDF using reportlab
"""

__docformat__ = 'reStructuredText'


import createpdf
from docutils import writers
from StringIO import StringIO

class Writer(writers.Writer):

    supported = ('pdf')
    """Formats this writer supports."""

    config_section = 'pdf writer'
    config_section_dependencies = ('writers',)

    output = None
    """Final translated form of `document`."""

    def translate(self):
        sio=StringIO()
        createpdf.createPdf(doctree=self.document,output=sio)        
        self.output=sio.getvalue()

    def supports(self, format):
        """This writer supports all format-specific elements."""
        return 1

if __name__ == "__main__":
    from docutils.core import publish_cmdline, default_description

    description = ('Generates pseudo-XML from standalone reStructuredText '
                   'sources (for testing purposes).  ' + default_description)

    publish_cmdline(writer=Writer(),description=description)
