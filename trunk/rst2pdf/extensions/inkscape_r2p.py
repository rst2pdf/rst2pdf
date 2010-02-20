# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

''' inkscape.py is an rst2pdf extension (e.g. rst2pdf -e inkscape xxx xxxx)
    which uses the inkscape program to convert an svg to a PDF, then uses
    the vectorpdf code to process the PDF.

    TODO: NOTE:

    The initial version is a proof of concept; uses subprocess in a naive way,
    and doesn't check return from inkscape for errors.
'''

import os, tempfile, subprocess
from weakref import WeakKeyDictionary

from vectorpdf import VectorPdf
import rst2pdf.image

class InkscapeImage(VectorPdf):

    # The filecache allows us to only read a given PDF file once
    # for every RstToPdf client object.  This allows this module
    # to usefully cache, while avoiding being the cause of a memory
    # leak in a long-running process.

    source_filecache = WeakKeyDictionary()

    @classmethod
    def available(self):
        return True

    def __init__(self, filename, width=None, height=None, kind='direct',
                                 mask=None, lazy=True, srcinfo=None):
        client, uri = srcinfo
        cache = self.source_filecache.setdefault(client, {})
        pdffname = cache.get(filename)
        if pdffname is None:
            tmpf, pdffname = tempfile.mkstemp(suffix='.pdf')
            os.close(tmpf)
            client.to_unlink.append(pdffname)
            cache[filename] = pdffname
            subprocess.call(['inkscape', filename, '-A', pdffname])
            self.load_xobj((client, pdffname))

        pdfuri = uri.replace(filename, pdffname)
        pdfsrc = client, pdfuri
        VectorPdf.__init__(self, pdfuri, width, height, kind, mask, lazy, pdfsrc)

def install(createpdf, options):
    ''' Monkey-patch our class in to image as a replacement class for SVGImage.
    '''
    rst2pdf.image.SVGImage = InkscapeImage
