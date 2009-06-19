# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import tempfile
import os

from reportlab.platypus import *
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import *

try:
    from aafigure import pdf
    from aafigure.aafigure import AsciiArtImage
    HAS_AAFIGURE=True
except ImportError:
    HAS_AAFIGURE=False

class AADrawingVisitor(pdf.PDFOutputVisitor):
    def __init__(self, scale = 1, line_width = 1,
                 foreground=  (0, 0, 0),
                 background = (255, 255, 255), 
                 fillcolor = (0, 0, 0),
                 proportional = False ):
        pdf.PDFOutputVisitor.__init__(self, None, scale, line_width,
                                      foreground, background, fillcolor, proportional)
    def visit_image(self, aa_image):
        """Process the given ASCIIArtFigure and output the shapes in
           the PDF file
        """
        self.aa_image = aa_image        # save for later XXX not optimal to do it here
        self.width = (aa_image.width)*aa_image.nominal_size*aa_image.aspect_ratio
        self.height = (aa_image.height)*aa_image.nominal_size
        self.drawing = Drawing(self._num(self.width), self._num(self.height))
        self.visit_shapes(aa_image.shapes)

class AAFigure(renderPDF.GraphicsFlowable):

    def __init__(self, text, scale = 1, line_width = 1,
                 foreground=  (0, 0, 0),
                 background = (255, 255, 255), 
                 fillcolor = (0, 0, 0),
                 proportional = False ):
        self.text = text
        if HAS_AAFIGURE:
            drawing=AADrawing(scale, line_width, foreground, background, fillcolor, proportional)
            figure=AsciiArtImage(self.text)
            drawing.visit_image(self.text)
            renderPDF.GraphicsFlowable.__init__(self,drawing.drawing)
        else:
            log.error('The aafigure directive requires you install aafigure')

if __name__ == "__main__":
    doc = SimpleDocTemplate("aafiguretest.pdf")
    Story = [AAFigure(r'0-->')]
    doc.build(Story)
