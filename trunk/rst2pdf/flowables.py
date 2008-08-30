# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$
__docformat__ = 'reStructuredText'

from reportlab.platypus import *
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
