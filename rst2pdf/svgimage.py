# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import os

from reportlab.platypus import Flowable, Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from log import log
from opt_imports import LazyImports

class SVGImage(Flowable):

    @classmethod
    def available(self):
        if LazyImports.svglib or LazyImports.uniconvertor:
            return True
        return False

    def __init__(self, filename, width=None, height=None, kind='direct',
                                     mask=None, lazy=True, srcinfo=None):
        Flowable.__init__(self)
        ext = os.path.splitext(filename)[-1]
        self._kind = kind
        # Prefer svglib for SVG, as it works better
        if ext in ('.svg', '.svgz') and LazyImports.svglib:
            self._mode = 'svglib'
            self.doc = LazyImports.svglib.svg2rlg(filename)
            self.imageWidth = width
            self.imageHeight = height
            x1, y1, x2, y2 = self.doc.getBounds()
            # Actually, svglib's getBounds seems broken.
            self._w, self._h = x2, y2
            if not self.imageWidth:
                self.imageWidth = self._w
            if not self.imageHeight:
                self.imageHeight = self._h
        # Use uniconvertor for the rest
        elif LazyImports.uniconvertor:
            load, plugins, self.uniconvertor_save = LazyImports.uniconvertor
            self._mode = 'uniconvertor'
            self.doc = load.load_drawing(filename.encode('utf-8'))
            self.saver = plugins.find_export_plugin(
                plugins.guess_export_plugin('.pdf'))
            self.imageWidth = width
            self.imageHeight = height
            x1, y1, x2, y2 = self.doc.BoundingRect()
            # The abs is to compensate for what appears to be
            # a bug in uniconvertor. At least doing it this way
            # I get the same values as in inkscape.
            # This fixes Issue 236
            self._w, self._h = abs(x2)-abs(x1), abs(y2)-abs(y1)
            
            if not self.imageWidth:
                self.imageWidth = self._w
            if not self.imageHeight:
                self.imageHeight = self._h
        else:
            self._mode = None
            log.error("Vector image support not enabled,"
                " please install svglib and/or uniconvertor.")
        self.__ratio = float(self.imageWidth)/self.imageHeight
        if kind in ['direct','absolute']:
            self.drawWidth = width or self.imageWidth
            self.drawHeight = height or self.imageHeight
        elif kind in ['bound','proportional']:
            factor = min(float(width)/self.imageWidth,float(height)/self.imageHeight)
            self.drawWidth = self.imageWidth*factor
            self.drawHeight = self.imageHeight*factor

    def wrap(self, aW, aH):
        return self.drawWidth, self.drawHeight

    def drawOn(self, canv, x, y, _sW=0):
        if _sW and hasattr(self, 'hAlign'):
            a = self.hAlign
            if a in ('CENTER', 'CENTRE', TA_CENTER):
                x += 0.5*_sW
            elif a in ('RIGHT', TA_RIGHT):
                x += _sW
            elif a not in ('LEFT', TA_LEFT):
                raise ValueError("Bad hAlign value " + str(a))
        canv.saveState()
        canv.translate(x, y)
        canv.scale(self.drawWidth/self._w, self.drawHeight/self._h)
        if self._mode == 'uniconvertor':
            self.uniconvertor_save(self.doc, open('.ignoreme.pdf', 'w'),
                '.ignoreme.pdf', options=dict(pdfgen_canvas=canv))
            os.unlink('.ignoreme.pdf')
        elif self._mode == 'svglib':
            self.doc._drawOn(canv)
        canv.restoreState()

class VectorImage(SVGImage):
    '''A class for non-SVG vector image formats. The main
    difference is that it is only available if uniconvertor is installed'''
    @classmethod
    def available(self):
        if LazyImports.uniconvertor:
            return True
        return False


if __name__ == "__main__":
    import sys
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate('svgtest.pdf')
    styles = getSampleStyleSheet()
    style = styles['Normal']
    Story = [Paragraph("Before the image", style),
             SVGImage(sys.argv[1]),
             Paragraph("After the image", style)]
    doc.build(Story)
