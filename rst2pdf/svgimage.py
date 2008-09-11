# -*- coding: utf-8 -*-

import sys,os
from reportlab.platypus import *

HAS_UNICONVERTOR=False

try:
    for p in sys.path:
        d=os.path.join(p,'uniconvertor')
        if os.path.isdir(d):
            sys.path.append(d)
            from app.io import load
            from app.plugins import plugins
            import app
            from uniconvsaver import save
            app.init_lib()
            plugins.load_plugin_configuration()
            HAS_UNICONVERTOR=True
            break
except ImportError:
    pass

class SVGImage(Flowable):
    def __init__(self,imgname):
        if HAS_UNICONVERTOR:
            self.doc = load.load_drawing(imgname)
            self.saver = plugins.find_export_plugin(plugins.guess_export_plugin(".pdf"))
        else:
            log.error("SVG image support not enabled, install uniconvertor")
        Flowable.__init__(self)
    
    def wrap(self,aW,aH):
        if HAS_UNICONVERTOR:            
            br=self.doc.BoundingRect()
            return br[2],br[3]
        return 0,0
    
    def drawOn(self,canv,x,y,_sW=0):
        if HAS_UNICONVERTOR:            
            canv.saveState()
            canv.translate(x,y)
            save (self.doc,open(".ignoreme.pdf","w"),".ignoreme.pdf",options={'pdfgen_canvas':canv})
            os.unlink(".ignoreme.pdf")
            canv.restoreState()
           
           
if __name__ == "__main__":
    from reportlab.lib.styles import getSampleStyleSheet
    doc = SimpleDocTemplate("svgtest.pdf")
    styles = getSampleStyleSheet()
    style= styles["Normal"]
    Story = [Paragraph("Before the image",style),
             SVGImage(sys.argv[1]),
             Paragraph("After the image",style)]
    doc.build(Story)
    