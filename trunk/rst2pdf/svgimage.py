# -*- coding: utf-8 -*-

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


class SVGImage(Flowable):

    def __init__(self, filename, width=None, height=None):
        Flowable.__init__(self)
        if HAS_UNICONVERTOR:
            self.doc = load.load_drawing(filename)
            self.saver = plugins.find_export_plugin(plugins.guess_export_plugin(".pdf"))
            self.width = width
            self.height = height
            _, _, self._w, self._h = self.doc.BoundingRect()
            if not self.width:
                self.width = self._w
            if not self.height:
                self.height = self._h
        else:
            log.error("SVG image support not enabled, install uniconvertor")

    def wrap(self, aW, aH):
        if HAS_UNICONVERTOR:
            return self.width, self.height
        return 0, 0

    def drawOn(self, canv, x, y, _sW=0):
        if HAS_UNICONVERTOR:
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
            save(self.doc, open(".ignoreme.pdf","w"), ".ignoreme.pdf", options={'pdfgen_canvas': canv})
            os.unlink(".ignoreme.pdf")
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
