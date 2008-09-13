# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$
__docformat__ = 'reStructuredText'

from reportlab.platypus import *
from reportlab.platypus.doctemplate import *
from reportlab.lib.units import *
from reportlab.platypus.flowables import _listWrapOn, _FUZZ

from log import log
import styles

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

class DelayedTable(Flowable):
    '''A flowable that inserts a table for which it has the data.
    Needed so column widths can be determined after we know on what
    frame the table will be inserted, thus making the overal table width
    correct'''
    def __init__(self,data,colwidths,style):
        self.data=data
        self.colwidths=colwidths
        self.style=style
        self.t=None
    def wrap(self,w,h):
        # First create the table, with the widths from colwidths reinterpreted
        # if needed as percentages of frame/cell/whatever width w is.

        # Colwidths in ReST are relative: 10,10,10 means 33%,33%,33%
        # So, we need to calculate them relative to something
        # and we use the text width of the page. That sucks for
        # multicolumn pages
        # FIXME: make it work for multicolumn pages. No idea how, yet.
        _tw=w/sum(self.colwidths)
        colwidths=[ _w*_tw for _w in self.colwidths ]
        
        self.t=Table(self.data,colWidths=colwidths,style=TableStyle(self.style))
        return self.t.wrap(w,h)

    def split(self,w,h):
        return self.t.split(w,h)

    def drawOn(self,canvas,x,y,_sW=0):
        self.t.drawOn(canvas,x,y,_sW)

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

class SmartFrame(Frame):
    '''A (Hopefully) smarter frame object that knows how to
    handle a two-pass layout procedure (someday)'''

    def __init__(self, container,x1, y1, width,height, leftPadding=6, bottomPadding=6,
            rightPadding=6, topPadding=6, id=None, showBoundary=0,
            overlapAttachedSpace=None,_debug=None):
        self.container=container
        self.onSidebar=False
        Frame.__init__(self,x1, y1, width,height, leftPadding, bottomPadding,
            rightPadding, topPadding, id, showBoundary,
            overlapAttachedSpace,_debug)

class FrameCutter(FrameActionFlowable):
    def __init__(self,dx,width,flowable,padding,lpad,floatLeft=True):
        self.width=width
        self.dx=dx
        self.f=flowable
        self.padding=padding
        self.lpad=lpad
        self.floatLeft=floatLeft
    def frameAction(self,frame):
        idx=frame.container.frames.index(frame)
        if self.floatLeft:
            if self.width-self.padding > 30: # Don´ t bother inserting a silly thin frame
                f1=SmartFrame(frame.container,
                              frame._x1+self.dx-2*self.padding,
                              frame._y2-self.f.height-3*self.padding,
                              self.width+2*self.padding,
                              self.f.height+3*self.padding,bottomPadding=0,topPadding=0,
                              leftPadding=self.lpad)
                f1._atTop=frame._atTop
                # This is a frame next to a sidebar.
                f1.onSidebar=True
                frame.container.frames.insert(idx+1,f1)

            if frame._height-self.f.height-2*self.padding >30: # Don't add silly thin frame
                frame.container.frames.insert(idx+2,SmartFrame(frame.container,
                                                               frame._x1,
                                                               frame._y1p,
                                                               self.width+self.dx,
                                                               frame._height-self.f.height-3*self.padding,topPadding=0))
        else:
            if self.width-self.padding > 30: # Don´ t bother inserting a silly thin frame
                f1=SmartFrame(frame.container,
                              frame._x1-self.width,
                              frame._y2-self.f.height-2*self.padding,
                              self.width,
                              self.f.height+2*self.padding,bottomPadding=0,topPadding=0,
                              rightPadding=self.lpad)
                f1._atTop=frame._atTop
                # This is a frame next to a sidebar.
                f1.onSidebar=True
                frame.container.frames.insert(idx+1,f1)
            if frame._height-self.f.height-2*self.padding >30:
                frame.container.frames.insert(idx+2,SmartFrame(frame.container,
                    frame._x1-self.width,
                    frame._y1p,
                    self.width+self.dx,
                    frame._height-self.f.height-2*self.padding,
                    topPadding=0))
                    
class Sidebar(FrameActionFlowable):
    def __init__(self,flowables,style):
        self.style=style
        self.width=self.style.width
        self.flowables=flowables

    def frameAction(self,frame):
        if frame.onSidebar: #We are still on the frame next to a sidebar!
            frame._generated_content = [FrameBreak(),self]
        else:
            w=frame.container.styles.adjustUnits(self.width,frame.width)
            idx=frame.container.frames.index(frame)
            padding = self.style.borderPadding
            width=self.style.width
            self.style.padding=frame.container.styles.adjustUnits(str(padding),frame.width)
            self.style.width=frame.container.styles.adjustUnits(str(width),frame.width)
            self.kif=BoxedContainer(self.flowables,self.style)
            if self.style.float=='left':
                self.style.lpad = frame.leftPadding
                f1=SmartFrame(frame.container,
                            frame._x1,
                            frame._y1p,
                            w-2*self.style.padding,
                            frame._y-frame._y1p,
                            leftPadding=self.style.lpad,
                            rightPadding=0,
                            bottomPadding=0,
                            topPadding=0)
                f1._atTop=frame._atTop
                frame.container.frames.insert(idx+1,f1)
                frame._generated_content = [FrameBreak(),self.kif,
                    FrameCutter(w,
                        frame.width-w,
                        self.kif,
                        padding,
                        self.style.lpad,
                        True),
                    FrameBreak()]
            elif self.style.float=='right':
                self.style.lpad = frame.rightPadding
                frame.container.frames.insert(idx+1,SmartFrame(frame.container,
                                                        frame._x1+frame.width-self.style.width,
                                                        frame._y1p,
                                                        w,
                                                        frame._y-frame._y1p,
                                                        rightPadding=self.style.lpad,
                                                        leftPadding=0,
                                                        bottomPadding=0,
                                                        topPadding=0))
                frame._generated_content = [FrameBreak(),self.kif,
                    FrameCutter(w,
                        frame.width-w,
                        self.kif,
                        padding,
                        self.style.lpad,
                        False),
                    FrameBreak()]


class BoundByWidth(Flowable):
    '''Limits a list of flowables by width, but still lets them break
    over pages and frames'''
    
    def __init__(self, maxWidth, content=[], style=None, mode=None):
        self.maxWidth=maxWidth
        self.content=content
        self.style=style
        self.mode=mode
        if self.style:
            self.pad = self.style.borderPadding+self.style.borderWidth+.1
        else:
            self.pad=0
        Flowable.__init__(self)

    def identity(self, maxLen=None):
        return "<%s at %s%s%s> size=%sx%s" % (self.__class__.__name__, hex(id(self)), self._frameName(),
                getattr(self,'name','') and (' name="%s"'% getattr(self,'name','')) or '',
                getattr(self,'maxWidth','') and (' maxWidth=%s'%str(getattr(self,'maxWidth',0))) or '',
                getattr(self,'maxHeight','')and (' maxHeight=%s' % str(getattr(self,'maxHeight')))or '')

    def wrap(self,availWidth,availHeight):
        '''If we need more width than we have, complain, keep a scale'''
        if self.style:
            self.pad = self.style.borderPadding+self.style.borderWidth+.1
        else:
            self.pad=0
        maxWidth = float(min(styles.adjustUnits(self.maxWidth,availWidth) or availWidth,availWidth))
        self.maxWidth=maxWidth
        maxWidth -= 2*self.pad
        self.width, self.height = _listWrapOn(self.content,maxWidth,self.canv)
        self.scale=1.0
        if self.width > maxWidth:
            log.warning("BoundByWidth too wide to fit in frame: %s",self.identity())
            if self.mode=='shrink':
                self.scale=(maxWidth+2*self.pad)/(self.width+2*self.pad)
                self.height=self.height*self.scale
            #self.width=maxWidth
        # No need to warn here, it will just split
        #if self.height+2*self.pad*self.scale > availHeight:
            #log.warning("BoundByWidth too tall to fit in frame: %s",self.identity())
        return self.width, self.height+2*self.pad*self.scale

    def split(self,availWidth,availHeight):
        if len(self.content)>1:
            # Try splitting in our individual elements
            return [ BoundByWidth(self.maxWidth,[f],self.style,self.mode) for f in self.content ]
        else: # We need to split the only element we have
            return [ BoundByWidth(self.maxWidth,[f],self.style,self.mode) for f in self.content[0].split(availWidth-2*self.pad,availHeight-2*self.pad) ]

    def draw(self):
        '''we simulate being added to a frame'''
        canv=self.canv
        canv.saveState()
        x=canv._x
        y=canv._y
        _sW=0
        scale=self.scale
        content=None
        aW=None
        #, canv, x, y, _sW=0, scale=1.0, content=None, aW=None):
        pS = 0
        if aW is None: aW = self.width
        aW = scale*(aW+_sW)
        if content is None:
            content = self.content
        y += (self.height+self.pad)/scale
        x += self.pad
        for c in content:
            w, h = c.wrapOn(canv,aW,0xfffffff)
            if (w<_FUZZ or h<_FUZZ) and not getattr(c,'_ZEROSIZE',None): continue
            if c is not content[0]: h += max(c.getSpaceBefore()-pS,0)
            y -= h
            canv.saveState()
            if self.mode=='shrink':
                canv.scale(scale,scale)
            elif self.mode=='truncate':
                p=canv.beginPath()
                p.rect(x-self.pad,y-self.pad,self.maxWidth,self.height+2*self.pad)
                canv.clipPath(p,stroke=0)
            c.drawOn(canv,x,y,_sW=aW-w)
            canv.restoreState()
            if c is not content[-1]:
                pS = c.getSpaceAfter()
                y -= pS
        canv.restoreState()

class BoxedContainer(BoundByWidth):
    def __init__(self, content, style, mode='shrink'):
        BoundByWidth.__init__(self,style.width, content, mode=mode, style=None)
        self.style=style
        self.mode=mode

    def draw(self):
        canv=self.canv
        canv.saveState()
        x=canv._x
        y=canv._y
        _sW=0
        lw=0
        if self.style and self.style.borderWidth >0:
            lw=self.style.borderWidth
            canv.setLineWidth(self.style.borderWidth)
            canv.setStrokeColor(self.style.borderColor)
        if self.style and self.style.backColor:
            canv.setFillColor(self.style.backColor)
        if self.style and self.style.padding:
            self.padding=self.style.padding
        else:
            self.padding=0
        self.padding+=lw
        p = canv.beginPath()
        p.rect(x, y, self.width+2*self.padding,self.height+2*self.padding)
        canv.drawPath(p,stroke=1,fill=1)
        canv.restoreState()
        BoundByWidth.draw(self)
        
    def split(self,availWidth,availHeight):
        if len(self.content)>1:
            # Try splitting in our individual elements
            return [ BoxedContainer([f],self.style,self.mode) for f in self.content ]
        else: # We need to split the only element we have
            return [ BoxedContainer([f],self.style,self.mode) for f in self.content[0].split(availWidth-2*self.pad,availHeight-2*self.pad) ]

if reportlab.Version == '2.1':

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
