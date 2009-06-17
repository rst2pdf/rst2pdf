# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import sys
import os

from reportlab.platypus import *

from log import log

HAS_UNICONVERTOR = False

try:
    for p in sys.path:
        d = os.path.join(p,'uniconvertor')
        if os.path.isdir(d):
            sys.path.append(d)
            from app.io import load
            from app.plugins import plugins
            import app
            from uniconvsaver import save
            app.init_lib()
            plugins.load_plugin_configuration()
            HAS_UNICONVERTOR = True
            break
except ImportError:
    pass

try:
    from svglib import svglib
except ImportError:
    svglib = None


class SVGImage(Flowable):

    def __init__(self, filename, width=None, height=None, kind='direct'):
        Flowable.__init__(self)
        ext = os.path.splitext(filename)[-1]
        self._mode=None
        self._kind=kind
        # Prefer svglib for SVG, as it works better
        if ext in ('.svg', '.svgz') and svglib is not None:
            self.doc = svglib.svg2rlg(filename)
            self.width=width
            self.height=height
            _,_,self._w,self._h=self.doc.getBounds()
            if not self.width: 
                self.width=self._w
            if not self.height: 
                self.height=self._h
            self._mode='svglib'
        # Use uniconvertor for the rest
        elif HAS_UNICONVERTOR:
            self.doc = load.load_drawing(filename)
            self.saver = plugins.find_export_plugin(plugins.guess_export_plugin(".pdf"))
            self.width = width
            self.height = height
            _, _, self._w, self._h = self.doc.BoundingRect()
            if not self.width:
                self.width = self._w
            if not self.height:
                self.height = self._h                
            self._mode='uniconvertor'
        else:
            log.error("Vector image support not enabled, install svglib or uniconvertor")
        self.__ratio=float(self.width)/self.height

    def wrap(self, aW, aH):
        if self._mode:
            if self._kind=='percentage_of_container':
                w, h= self.width, self.height
                if not w:
                    log.warning('Scaling image as % of container with w unset.'
                    'This should not happen, setting to 100')
                    w = 100
                scale=w/100.
                w = aW*scale
                h = w/self.__ratio
                self.width, self.height = w, h
                return w, h                
            else:
                return self.width, self.height
        return 0, 0

    def drawOn(self, canv, x, y, _sW=0):
        if self._mode:
            if _sW and hasattr(self,'hAlign'):
                from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
                a = self.hAlign
                if a in ('CENTER', 'CENTRE', TA_CENTER):
                    x += 0.5*_sW
                elif a in ('RIGHT', TA_RIGHT):
                    x += _sW
                elif a not in ('LEFT', TA_LEFT):
                    raise ValueError, "Bad hAlign value " + str(a)
            canv.saveState()
            canv.translate(x, y)
            canv.scale(self.width/self._w, self.height/self._h)
            if self._mode=='uniconvertor':
                save(self.doc, open(".ignoreme.pdf","w"), ".ignoreme.pdf", options={'pdfgen_canvas': canv})
                os.unlink(".ignoreme.pdf")
            elif self._mode=='svglib':
                self.doc._drawOn(canv)
            canv.restoreState()


if __name__ == "__main__":
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate("svgtest.pdf")
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    Story = [Paragraph("Before the image", style),
             SVGImage(sys.argv[1]),
             Paragraph("After the image", style)]
    doc.build(Story)
