# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import sys
import os

from reportlab.platypus import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

import pdfrw
from pdfrw.toreportlab import makerl
from pdfrw.buildxobj import CacheXObj

from rst2pdf.log import log
import rst2pdf.image
from rst2pdf.opt_imports import LazyImports

# This is kinda goofy -- since we bring it in as a subpackage,
# go ahead and monkey patch it in.

LazyImports.pdfinfo = pdfrw

        # TODO:  Looks the same as for other images, because I
        #        stole it from other image handlers.  Common base class???

class VectorPdf(Flowable):

    # TODO: Really need some way to uncache this between runs
    load_xobj = CacheXObj().load

    def __init__(self, filename, width=None, height=None, kind='direct', mask=None, lazy=True):
        Flowable.__init__(self)
        self._kind = kind
        self.xobj = self.load_xobj(filename)
        self.imageWidth = width
        self.imageHeight = height
        x1, y1, x2, y2 = self.xobj.BBox

        self._w, self._h = x2 - x1, y2 - y1
        if not self.imageWidth:
            self.imageWidth = self._w
        if not self.imageHeight:
            self.imageHeight = self._h
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
        if _sW > 0 and hasattr(self, 'hAlign'):
            a = self.hAlign
            if a in ('CENTER', 'CENTRE', TA_CENTER):
                x += 0.5*_sW
            elif a in ('RIGHT', TA_RIGHT):
                x += _sW
            elif a not in ('LEFT', TA_LEFT):
                raise ValueError("Bad hAlign value " + str(a))

        xobj = self.xobj
        xobj_name = makerl(canv._doc, xobj)
        x -= xobj.BBox[0]
        y -= xobj.BBox[1]

        canv.saveState()
        canv.translate(x, y)
        canv.scale(self.drawWidth/self._w, self.drawHeight/self._h)
        canv.doForm(xobj_name)
        canv.restoreState()

rst2pdf.image.VectorPdf = VectorPdf
