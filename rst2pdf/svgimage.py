# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Flowable, Paragraph
from svglib.svglib import svg2rlg


class SVGImage(Flowable):
    def __init__(
        self,
        filename,
        width=None,
        height=None,
        kind='direct',
        mask=None,
        lazy=True,
        srcinfo=None,
    ):
        Flowable.__init__(self)
        self._kind = kind
        self._mode = 'svg2rlg'
        self.doc = svg2rlg(filename)
        self.imageWidth = width
        self.imageHeight = height
        x1, y1, x2, y2 = self.doc.getBounds()
        # Actually, svg2rlg's getBounds seems broken.
        self._w, self._h = x2, y2
        if not self.imageWidth:
            self.imageWidth = self._w
        if not self.imageHeight:
            self.imageHeight = self._h
        self.__ratio = float(self.imageWidth) / self.imageHeight
        if kind in ['direct', 'absolute']:
            self.drawWidth = width or self.imageWidth
            self.drawHeight = height or self.imageHeight
        elif kind in ['bound', 'proportional']:
            factor = min(
                float(width) / self.imageWidth,
                float(height) / self.imageHeight,
            )
            self.drawWidth = self.imageWidth * factor
            self.drawHeight = self.imageHeight * factor

    def wrap(self, aW, aH):
        return self.drawWidth, self.drawHeight

    def drawOn(self, canv, x, y, _sW=0):
        if _sW and hasattr(self, 'hAlign'):
            a = self.hAlign
            if a in ('CENTER', 'CENTRE', TA_CENTER):
                x += 0.5 * _sW
            elif a in ('RIGHT', TA_RIGHT):
                x += _sW
            elif a not in ('LEFT', TA_LEFT):
                raise ValueError("Bad hAlign value " + str(a))
        canv.saveState()
        canv.translate(x, y)
        canv.scale(self.drawWidth / self._w, self.drawHeight / self._h)
        self.doc._drawOn(canv)
        canv.restoreState()


if __name__ == "__main__":
    import sys
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate('svgtest.pdf')
    styles = getSampleStyleSheet()
    style = styles['Normal']
    Story = [
        Paragraph("Before the image", style),
        SVGImage(sys.argv[1]),
        Paragraph("After the image", style),
    ]
    doc.build(Story)
