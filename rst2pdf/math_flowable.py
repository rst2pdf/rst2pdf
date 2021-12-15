# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import os
import re
import tempfile

from reportlab.platypus.flowables import Flowable
from reportlab.platypus import SimpleDocTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .log import log

try:
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties
    from matplotlib.colors import ColorConverter

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

fonts = {}


def enclose(s):
    """Enclose the string in $...$ if needed"""
    if not re.match(r'.*\$.+\$.*', s, re.MULTILINE | re.DOTALL):
        s = u"$%s$" % s
    return s


class Math(Flowable):
    def __init__(self, s, label=None, fontsize=12, color='black'):
        self.s = s
        self.label = label
        self.fontsize = fontsize
        self.color = color
        if HAS_MATPLOTLIB:
            self.parser = mathtext.MathTextParser("Path")
        else:
            log.error(
                "Math support not available,"
                " some parts of this document will be rendered incorrectly."
                " Install matplotlib."
            )
        Flowable.__init__(self)
        self.hAlign = 'CENTER'

    def wrap(self, aW, aH):
        if HAS_MATPLOTLIB:
            try:
                (width, height, descent, _, _,) = self.parser.parse(
                    enclose(self.s), 72, prop=FontProperties(size=self.fontsize)
                )
                return width, height
            except Exception as e:
                log.error(f"Math error in wrap: {e}")
                pass

        return 10, 10

    def drawOn(self, canv, x, y, _sW=0):
        if _sW and hasattr(self, 'hAlign'):
            from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

            a = self.hAlign
            if a in ('CENTER', 'CENTRE', TA_CENTER):
                x = x + 0.5 * _sW
            elif a in ('RIGHT', TA_RIGHT):
                x = x + _sW
            elif a not in ('LEFT', TA_LEFT):
                raise ValueError("Bad hAlign value " + str(a))
        height = 0
        if HAS_MATPLOTLIB:
            global fonts
            canv.saveState()
            canv.translate(x, y)
            try:
                (width, height, descent, glyphs, rects,) = self.parser.parse(
                    enclose(self.s), 72, prop=FontProperties(size=self.fontsize)
                )

                for font, fontsize, num, ox, oy in glyphs:
                    fontname = font.fname
                    if fontname not in fonts:
                        fonts[fontname] = fontname
                        pdfmetrics.registerFont(TTFont(fontname, fontname))
                    canv.setFont(fontname, fontsize)
                    col_conv = ColorConverter()
                    rgb_color = col_conv.to_rgb(self.color)
                    canv.setFillColorRGB(rgb_color[0], rgb_color[1], rgb_color[2])
                    canv.drawString(ox, oy, chr(num))

                canv.setLineWidth(0)
                canv.setDash([])
                for ox, oy, width, height in rects:
                    canv.rect(ox, oy + 2 * height, width, height, fill=1)
            except Exception as e:
                log.error(f"Math error: {e}")
                col_conv = ColorConverter()
                rgb_color = col_conv.to_rgb(self.color)
                canv.setFillColorRGB(rgb_color[0], rgb_color[1], rgb_color[2])
                canv.drawString(0, 0, self.s)
            canv.restoreState()
        else:
            canv.saveState()
            canv.drawString(x, y, self.s)
            canv.restoreState()
        if self.label:
            log.info('Drawing equation-%s' % self.label)
            canv.bookmarkHorizontal('equation-%s' % self.label, 0, height)

    def descent(self):
        """Return the descent of this flowable,
        useful to align it when used inline."""
        if HAS_MATPLOTLIB:
            width, height, descent, glyphs, rects = self.parser.parse(
                enclose(self.s), 72, prop=FontProperties(size=self.fontsize)
            )
            return descent
        return 0

    def genImage(self):
        """Create a PNG from the contents of this flowable.

        Required so we can put inline math in paragraphs.
        Returns the file name.
        The file is caller's responsibility.

        """

        s = enclose(self.s)

        fh, fn = tempfile.mkstemp(suffix=".png")
        os.close(fh)
        mathtext.math_to_image(s, fn, prop=None, dpi=None, format='png')
        return fn


if __name__ == "__main__":
    doc = SimpleDocTemplate("mathtest.pdf")
    Story = [
        Math(r'\mathcal{R}\prod_{i=\alpha\mathcal{B}}' r'^\infty a_i\sin(2 \pi f x_i)')
    ]
    doc.build(Story)
