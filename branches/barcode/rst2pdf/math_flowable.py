from reportlab.platypus import *
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from log import log
import tempfile,os

HAS_MATPLOTLIB=False
try:
    from matplotlib import mathtext
    HAS_MATPLOTLIB=True
except ImportError:
    pass

fonts={}

class Math(Flowable):
    def __init__(self,s):
        self.s=s
        if HAS_MATPLOTLIB:
            self.parser=mathtext.MathTextParser("Pdf")
        else:
            log.error("Math support not available, some parts of this document will be rendered incorrectly. Install matplotlib.")
        Flowable.__init__(self)
      
    def wrap(self,aW,aH):
        if HAS_MATPLOTLIB:
            width, height, descent, glyphs, rects, used_characters = \
            self.parser.parse('$%s$'%self.s, 72)
            return width, height
        return 10,10

    def drawOn(self,canv,x,y,_sW=0):
        if HAS_MATPLOTLIB:
            global fonts
            width, height, descent, glyphs, rects, used_characters = \
            self.parser.parse('$%s$'%self.s, 72)
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
            canv.saveState()
            canv.drawString(x,y,self.s)
            canv.restoreState()

    def descent(self):
        '''Returns the descent of this flowable, useful to align it when used inline'''
        if HAS_MATPLOTLIB:
            width, height, descent, glyphs, rects, used_characters = \
            self.parser.parse('$%s$'%self.s, 72)
            return descent
        return 0

    def genImage(self):
        '''Create a PNG from the contents of this flowable. Required so we can
        put inline math in paragraphs. Returns the file name. The file
        is caller's responsability'''
        dpi=72
        scale=10
        import Image,ImageFont,ImageDraw,ImageColor
        if not HAS_MATPLOTLIB:
            img=Image.new('L',(120,120),ImageColor.getcolor("black","L"))
        else:
            width, height, descent, glyphs, rects, used_characters = \
            self.parser.parse('$%s$'%self.s,dpi)
            img=Image.new('L',(int(width*scale),int(height*scale)),ImageColor.getcolor("white","L"))
            draw=ImageDraw.Draw(img)
            for ox, oy, fontname, fontsize, num, symbol_name in glyphs:
                font=ImageFont.truetype(fontname,int(fontsize*scale))
                tw,th=draw.textsize(unichr(num),font=font)
                # No, I don't understand why that 4 is there. As we used to say in the pure math
                # department, that was a numerical solution.
                draw.text((ox*scale,(height-oy-fontsize+4)*scale),unichr(num),font=font)

            for ox, oy, w, h in rects:
                x1=ox*scale
                x2=x1+w*scale
                y1=(height-oy)*scale
                y2=y1+h*scale
                draw.rectangle([x1,y1,x2,y2],fill=ImageColor.getcolor("black","L"))
        fh,fn=tempfile.mkstemp(suffix=".png")
        os.close(fh)
        img.save(fn)
        return fn
        
        

if __name__ == "__main__":
    doc = SimpleDocTemplate("mathtest.pdf")
    Story=[Math(r'$\mathcal{R}\prod_{i=\alpha\mathcal{B}}^\infty a_i\sin(2 \pi f x_i)$')]
    doc.build(Story)
