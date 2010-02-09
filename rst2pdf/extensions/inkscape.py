# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

''' inkscape.py is an rst2pdf extension (e.g. rst2pdf -e inkscape xxx xxxx)
    which uses the inkscape program to convert an svg to a PDF, then uses
    the vectorpdf code to process the PDF.

    TODO: NOTE:

    The initial version is a proof of concept; uses subprocess in a naive way,
    doesn't check return from inkscape for errors, doesn't cache images, etc.,
    so this will have to be cleaned up for production use.

    ALSO, I think the way this is used, two instances will be created and
    destroyed (invoking inkscape twice for every image), so that's a bit
    wasteful...
'''

import os, tempfile, subprocess

from vectorpdf import VectorPdf
import rst2pdf.image

class InkscapeImage(VectorPdf):

    @classmethod
    def available(self):
        return True

    def __init__(self, filename, width=None, height=None, kind='direct', mask=None, lazy=True):
        tmpf, tmpname = tempfile.mkstemp(suffix='.pdf')
        os.close(tmpf)
        subprocess.call(['inkscape', filename, '-A', tmpname])
        VectorPdf.__init__(self, tmpname, width, height, kind, mask, lazy)
        os.unlink(tmpname)

def install():
    ''' Monkey-patch our class in to image as a replacement class for SVGImage.
    '''
    rst2pdf.image.SVGImage = InkscapeImage
