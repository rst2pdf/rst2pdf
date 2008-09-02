# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$
__docformat__ = 'reStructuredText'

from reportlab.platypus import *
from reportlab.platypus.doctemplate import *
from reportlab.lib.units import *

class MyIndenter(Indenter):
    '''I can't remember why this exists'''
    def draw(self):
        pass
    width=0
    height=0

class OutlineEntry(Flowable):
    '''Creates outline entries in the PDF TOC'''
    def __init__(self,label,text,level=0,snum=None):
        '''* label is a unique label.
           * text is the text to be displayed in the outline tree
           * level is the level, 0 is outermost, 1 is child of 0, etc.
        '''
        if label is None: # it happens
            self.label=text.replace(u'\xa0', ' ').strip(
                ).replace(' ', '_').encode('ascii', 'replace')
        else:
            self.label=label.strip()
        self.text=text.strip()
        self.level=int(level)
        self.snum=snum
        Flowable.__init__(self)

    def wrap(self,w,h):
        '''This takes no space'''
        return (0,0)

    def draw(self):
        self.canv.bookmarkPage(self.label)
        self.canv.sectName=self.text
        if self.snum is not None:
            self.canv.sectNum=self.snum
        else:
            self.canv.sectNum=""
        self.canv.addOutlineEntry(self.text,
                                  self.label,
                                  self.level, False)

    def __repr__(self):
        return "OutlineEntry (label=%s , text=%s , level=%d) \n"%(self.label,self.text,self.level)

class Separation(Flowable):
    """A simple <hr>-like flowable"""

    def wrap(self,w,h):
        self.w=w
        return (w,1*cm)

    def draw(self):
        self.canv.line(0,0.5*cm,self.w,0.5*cm)

class Reference(Flowable):
    '''A flowable to insert an anchor without taking space'''
    def __init__(self,refid):
        self.refid=refid
        Flowable.__init__(self)
        
    def wrap(self,w,h):
        '''This takes no space'''
        return (0,0)

    def draw(self):
        self.canv.bookmarkPage(self.refid)

    def repr(self):
        return "Anchor: %s"%self.refid


class SmartFrame(Frame):
    '''A (Hopefully) smarter frame object that knows how to
    handle a two-pass layout procedure'''

    def __init__(self, container,x1, y1, width,height, leftPadding=6, bottomPadding=6,
            rightPadding=6, topPadding=6, id=None, showBoundary=0,
            overlapAttachedSpace=None,_debug=None):
        self.container=container
        Frame.__init__(self,x1, y1, width,height, leftPadding, bottomPadding,
            rightPadding, topPadding, id, showBoundary,
            overlapAttachedSpace,_debug)

class FrameCutter(FrameActionFlowable):
    def __init__(self,dx,width,flowable):
        self.width=width
        self.dx=dx
        self.f=flowable
    def frameAction(self,frame):
        idx=frame.container.frames.index(frame)
        if self.width-6 > 10: # Don´ t bother inserting a silly thin frame
            frame.container.frames.insert(idx+1,SmartFrame(frame.container,frame._x1+self.dx+6,
                                                           frame._y2-self.f.height-12,self.width-6,
                                                           self.f.height+12,bottomPadding=0,topPadding=6,leftPadding=0))
        frame.container.frames.insert(idx+2,SmartFrame(frame.container,frame._x1,frame._y1p,
                                                        self.width+self.dx,frame._height-self.f.height-12,topPadding=0))

class BoxedContainer(KeepInFrame):
    def __init__(self, content, style, mergeSpace=1, mode='shrink', name=''):
        self.style=style
        KeepInFrame.__init__(self,self.style.width, 200*cm, content, mergeSpace, mode, name)

    def drawOn(self,canv,x,y,_sW=0):
        canv.saveState()
        if self.style.borderWidth >0:
            canv.setLineWidth(self.style.borderWidth)
            canv.setStrokeColor(self.style.borderColor)
        if self.style.backColor:
            canv.setFillColor(self.style.backColor)
        p = canv.beginPath()
        p.rect(x, y, self.width+6,self.height+3)
        canv.drawPath(p,stroke=1,fill=1)
        canv.restoreState()
        KeepInFrame.drawOn(self,canv,x+3,y,_sW)

class Sidebar(FrameActionFlowable):
    def __init__(self,flowables,style):
        self.style=style
        self.width=self.style.width
        self.kif=BoxedContainer(flowables,style)

    def frameAction(self,frame):
        print frame.__dict__
        w=frame.container.styles.adjustUnits(self.width,frame.width)
        idx=frame.container.frames.index(frame)
        frame.container.frames.insert(idx+1,SmartFrame(frame.container,frame._x1,frame._y1p,
                                                       w,frame._y-frame._y1p,leftPadding=6,bottomPadding=6,topPadding=6))
        frame._generated_content = [FrameBreak(),self.kif,FrameCutter(w,frame.width-w,self.kif),FrameBreak()]

class MyPageBreak(FrameActionFlowable):
    def __init__(self, templateName=None):
        self.templateName=templateName

    def frameAction(self,frame):
        if not frame._atTop:
            frame._generated_content = [SetNextTemplate(self.templateName),PageBreak()]
        else:
            frame._generated_content = [SetNextTemplate(self.templateName)]

class SetNextTemplate(Flowable):
    """
    Sets canv.templateName when drawing.

    rst2pdf uses that to switch page templates.
    """

    def __init__(self, templateName=None):
        self.templateName=templateName
        Flowable.__init__(self)
        
    def draw(self):
        if self.templateName:
            self.canv.templateName=self.templateName


import reportlab.platypus.paragraph as pla_para

################Ugly stuff below

def _do_post_text(i, t_off, tx):
    '''From reportlab's paragraph.py, patched to avoid underlined links'''
    xs = tx.XtraState
    leading = xs.style.leading
    ff = 0.125*xs.f.fontSize
    y0 = xs.cur_y - i*leading
    y = y0 - ff
    ulc = None
    for x1,x2,c in xs.underlines:
        if c!=ulc:
            tx._canvas.setStrokeColor(c)
            ulc = c
        tx._canvas.line(t_off+x1, y, t_off+x2, y)
    xs.underlines = []
    xs.underline=0
    xs.underlineColor=None

    ys = y0 + 2*ff
    ulc = None
    for x1,x2,c in xs.strikes:
        if c!=ulc:
            tx._canvas.setStrokeColor(c)
            ulc = c
        tx._canvas.line(t_off+x1, ys, t_off+x2, ys)
    xs.strikes = []
    xs.strike=0
    xs.strikeColor=None

    yl = y + leading
    for x1,x2,link in xs.links:
        # This is the bad line
        #tx._canvas.line(t_off+x1, y, t_off+x2, y)
        _doLink(tx, link, (t_off+x1, y, t_off+x2, yl))
    xs.links = []
    xs.link=None

# Look behind you! A three-headed monkey!
pla_para._do_post_text.func_code = _do_post_text.func_code

############### End of the ugly
