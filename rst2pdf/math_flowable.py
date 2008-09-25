from reportlab.platypus import *
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from log import log

HAS_MATPLOTLIB=False
try:
    from matplotlib import mathtext
    HAS_MATPLOTLIB=True
except ImportError:
    pass

fonts={}

class Math(Flowable):
    def __init__(self,s):
        if HAS_MATPLOTLIB:
            self.s=s
            self.parser=mathtext.MathTextParser("Pdf")
        else:
            log.error("Math support not available, install matplotlib")
        Flowable.__init__(self)
      
    def wrap(self,aW,aH):
        if HAS_MATPLOTLIB:
            print "S:",self.s
            width, height, descent, glyphs, rects, used_characters = \
            self.parser.parse(self.s, 72)
            return width, height
        return 0,0

    def drawOn(self,canv,x,y,_sW=0):
        if HAS_MATPLOTLIB:
            global fonts
            width, height, descent, glyphs, rects, used_characters = \
            self.parser.parse(self.s, 72)
            canv.saveState()
            canv.translate(x,y)
            for ox, oy, fontname, fontsize, num, symbol_name in glyphs:
                if not fontname in fonts:
                    fonts[fontname]=fontname
                    pdfmetrics.registerFont(TTFont(fontname, fontname))
                canv.setFont(fontname,fontsize)
                canv.drawString(ox,oy,unichr(num))

            canv.setLineWidth(0)
            canv.setDash([])
            for ox, oy, width, height in rects:
                canv.rect(ox, oy+2*height, width, height,fill=1)

            canv.restoreState()
        else:
            return

if __name__ == "__main__":
    doc = SimpleDocTemplate("mathtest.pdf")
    Story=[Math(r'$\mathcal{R}\prod_{i=\alpha\mathcal{B}}^\infty a_i\sin(2 \pi f x_i)$')]
    doc.build(Story)
