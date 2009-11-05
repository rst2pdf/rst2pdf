# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import sys
import os

from reportlab.platypus import Flowable, Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from log import log

try:
    for p in sys.path:
        d = os.path.join(p, 'uniconvertor')
        if os.path.isdir(d):
            sys.path.append(d)
            from app.io import load
            from app.plugins import plugins
            import app
            from uniconvsaver import save
            app.init_lib()
            plugins.load_plugin_configuration()
            break
    else:
        raise ImportError
except ImportError:
    load = None

try:
    from svglib import svglib
except ImportError:
    svglib = None


class SVGImage(Flowable):

    @classmethod
    def available(self):
        if svglib is not None or load is not None:
            return True
        return False

    def __init__(self, filename, width=None, height=None, kind='direct', mask=None, lazy=True):
        Flowable.__init__(self)
        ext = os.path.splitext(filename)[-1]
        self._kind = kind
        # Prefer svglib for SVG, as it works better
        if ext in ('.svg', '.svgz') and svglib is not None:
            self._mode = 'svglib'
            self.doc = svglib.svg2rlg(filename)
            self.imageWidth = width
            self.imageHeight = height
            x1, y1, x2, y2 = self.doc.getBounds()
            self._w, self._h = x2-x1, y2-y1
            if not self.imageWidth:
                self.imageWidth = self._w
            if not self.imageHeight:
                self.imageHeight = self._h
        # Use uniconvertor for the rest
        elif load is not None:
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
        if self._mode:
            self.__ratio = float(self.imageWidth)/self.imageHeight
        if kind in ['direct','absolute']:
            self.drawWidth = width or self.imageWidth
            self.drawHeight = height or self.imageHeight
        elif kind in ['bound','proportional']:
            factor = min(float(width)/self.imageWidth,float(height)/self.imageHeight)
            self.drawWidth = self.imageWidth*factor
            self.drawHeight = self.imageHeight*factor

    def wrap(self, aW, aH):
        if self._mode:
            if self._kind == 'percentage_of_container':
                w, h = self.imageWidth, self.imageHeight
                if not w:
                    log.warning('Scaling image as % of container with w unset.'
                    'This should not happen, setting to 100')
                    w = 100
                scale = w/100.
                w = aW*scale
                h = w/self.__ratio
                self.imageWidth, self.imageHeight = w, h
                return w, h
            else:
                return self.imageWidth, self.imageHeight
        return 0, 0

    def drawOn(self, canv, x, y, _sW=0):
        if self._mode:
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
            canv.scale(self.imageWidth/self._w, self.imageHeight/self._h)
            if self._mode == 'uniconvertor':
                save(self.doc, open('.ignoreme.pdf', 'w'), '.ignoreme.pdf',
                    options=dict(pdfgen_canvas=canv))
                os.unlink('.ignoreme.pdf')
            elif self._mode == 'svglib':
                self.doc._drawOn(canv)
            canv.restoreState()

class VectorImage(SVGImage):
    '''A class for non-SVG vector image formats. The main
    difference is that it is only available if uniconvertor is installed'''
    @classmethod
    def available(self):
        if load is not None:
            return True
        return False


if __name__ == "__main__":
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate('svgtest.pdf')
    styles = getSampleStyleSheet()
    style = styles['Normal']
    Story = [Paragraph("Before the image", style),
             SVGImage(sys.argv[1]),
             Paragraph("After the image", style)]
    doc.build(Story)
