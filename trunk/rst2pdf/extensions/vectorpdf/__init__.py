# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import sys
import os
from weakref import WeakKeyDictionary

from reportlab.platypus import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

import pdfrw
from pdfrw.toreportlab import makerl
from pdfrw.buildxobj import CacheXObj

from rst2pdf.log import log
import rst2pdf.image
from rst2pdf.opt_imports import LazyImports

        # TODO:  Looks the same as for other images, because I
        #        stole it from other image handlers.  Common base class???

class VectorPdf(Flowable):

    # The filecache allows us to only read a given PDF file once
    # for every RstToPdf client object.  This allows this module
    # to usefully cache, while avoiding being the cause of a memory
    # leak in a long-running process.

    filecache = WeakKeyDictionary()

    @classmethod
    def load_xobj(cls, srcinfo):
        client, uri = srcinfo
        loader = cls.filecache.get(client)
        if loader is None:
            loader = cls.filecache[client] = CacheXObj().load
        return loader(uri)

    def __init__(self, filename, width=None, height=None, kind='direct',
                                     mask=None, lazy=True, srcinfo=None):
        Flowable.__init__(self)
        self._kind = kind
        self.xobj = self.load_xobj(srcinfo)
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

        xscale = self.drawWidth/self._w
        yscale = self.drawHeight/self._h

        x -= xobj.BBox[0] * xscale
        y -= xobj.BBox[1] * yscale

        canv.saveState()
        canv.translate(x, y)
        canv.scale(xscale, yscale)
        canv.doForm(xobj_name)
        canv.restoreState()

def install(createpdf, options):
    ''' Monkey-patch this PDF handling into rst2pdf
    '''
    LazyImports.pdfinfo = pdfrw
    rst2pdf.image.VectorPdf = VectorPdf
