# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import gzip
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from importlib.metadata import version

from packaging.version import Version
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Flowable, Paragraph
from svglib.svglib import svg2rlg

# svglib 1.x treated a bare SVG length as one point. svglib 2 maps one user
# unit to 0.75 pt. Undo that for unitless width/height so existing documents
# keep their size. svglib's own migration note is to scale by 4/3.
_USER_UNIT_TO_PT = 4.0 / 3.0
_PX_TO_PT = 0.75
_USER_UNIT_LENGTH = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")
# font-size:12px and font-size="12px". svglib 1.x converted an explicit px
# font size to points while leaving the coordinate system at 1 unit = 1 pt.
# After the coordinate scale above is undone, store that same point size.
_PX_FONT_SIZE = re.compile(
    r"(font-size\s*[:=]\s*[\"']?)"
    r"([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)"
    r"px\b",
    re.IGNORECASE,
)


def _svglib_uses_css_px():
    try:
        return Version(version("svglib")) >= Version("2")
    except Exception:
        return False


def _read_svg_text(filename):
    if str(filename).lower().endswith(".svgz"):
        with gzip.open(filename, "rt", encoding="utf-8") as handle:
            return handle.read()
    with open(filename, encoding="utf-8") as handle:
        return handle.read()


def _root_width_height(filename):
    # Only the root <svg> element matters, and it is the first start tag.
    source = filename
    handle = None
    if str(filename).lower().endswith(".svgz"):
        handle = gzip.open(filename, "rb")
        source = handle
    try:
        for _event, elem in ET.iterparse(source, events=("start",)):
            if elem.tag.rsplit("}", 1)[-1] == "svg":
                return elem.get("width"), elem.get("height")
            return None, None
    except ET.ParseError:
        return None, None
    finally:
        if handle is not None:
            handle.close()
    return None, None


def _is_user_unit(value):
    # Missing width/height follows the viewBox, which svglib 2 also scales.
    if value is None:
        return True
    return _USER_UNIT_LENGTH.match(value.strip()) is not None


def _rewrite_px_font_sizes(svg_text):
    def replace(match):
        size = float(match.group(2)) * _PX_TO_PT
        return f"{match.group(1)}{format(size, '.12g')}"

    return _PX_FONT_SIZE.sub(replace, svg_text)


def _restore_user_unit_size(drawing):
    drawing.width *= _USER_UNIT_TO_PT
    drawing.height *= _USER_UNIT_TO_PT
    drawing.scale(_USER_UNIT_TO_PT, _USER_UNIT_TO_PT)


def _svg2rlg(filename):
    """Load an SVG, preserving rst2pdf's historical user-unit size.

    Physical units (pt, mm, cm, in) and an explicit ``px`` viewport already
    agree between svglib 1.x and 2.x, so those files are left alone.
    """
    if not _svglib_uses_css_px():
        return svg2rlg(filename)

    width, height = _root_width_height(filename)
    if not (_is_user_unit(width) and _is_user_unit(height)):
        return svg2rlg(filename)

    svg_text = _read_svg_text(filename)
    rewritten = _rewrite_px_font_sizes(svg_text)
    if rewritten == svg_text:
        drawing = svg2rlg(filename)
    else:
        directory = os.path.dirname(os.path.abspath(filename)) or None
        try:
            descriptor, temporary = tempfile.mkstemp(suffix=".svg", dir=directory)
        except OSError:
            descriptor, temporary = tempfile.mkstemp(suffix=".svg")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(rewritten)
            drawing = svg2rlg(temporary)
        finally:
            try:
                os.remove(temporary)
            except OSError:
                pass
    if drawing is not None:
        _restore_user_unit_size(drawing)
    return drawing


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
        self.doc = _svg2rlg(filename)
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
