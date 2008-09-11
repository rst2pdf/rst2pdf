# -*- coding: utf-8 -*-

import sys,os
from app.io import load
from app.plugins import plugins
import app
from reportlab.platypus import *
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from uniconvsaver import save

app.init_lib()
plugins.load_plugin_configuration()


class SVGImage(Flowable):
    def __init__(self,imgname):
        self.doc = load.load_drawing(imgname)
        self.saver = plugins.find_export_plugin(plugins.guess_export_plugin(".pdf"))
        Flowable.__init__(self)
    
    def wrap(self,aW,aH):
        br=self.doc.BoundingRect()
        return br[2],br[3]
    
    def drawOn(self,canv,x,y,_sW=0):
        canv.saveState()
        canv.translate(x,y)
        save (self.doc,open(".ignoreme.pdf","w"),".ignoreme.pdf",options={'pdfgen_canvas':canv})
        os.unlink(".ignoreme.pdf")
        canv.restoreState()
        