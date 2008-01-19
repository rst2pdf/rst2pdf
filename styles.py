# -*- coding: utf-8 -*-

# Demo stylesheet module.for rst2pdf

from reportlab.platypus import *
import reportlab.lib.colors as colors
from reportlab.lib.units import *
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.lib.styles import *
from reportlab.lib.enums import *
from reportlab.pdfbase import pdfmetrics

import os

# Set these, and then **maybe** think of setting the stylesheets below
# if you want finer control

stdFont       = 'Helvetica'
stdBold       = 'Helvetica-Bold'
stdItalic     = 'Helvetica-Oblique'
stdBoldItalic = 'Helvetica-BoldOblique'
stdMono       = 'Courier'



# You can embed your own fonts and use them later if you want

if os.path.isfile('wrabbit/WHITRABT.TTF'):
    pdfmetrics.registerFont(TTFont('WhiteRabbit', 'wrabbit/WHITRABT.TTF'))
    addMapping('WhiteRabbit', 0, 0, 'WhiteRabbit')    #normal
    addMapping('WhiteRabbit', 0, 1, 'WhiteRabbit')    #italic
    addMapping('WhiteRabbit', 1, 0, 'WhiteRabbit')    #bold
    addMapping('WhiteRabbit', 1, 1, 'WhiteRabbit')    #italic and bold
    stdMono = 'WhiteRabbit'

def getStyleSheet():
    """Returns a stylesheet object"""
    stylesheet = StyleSheet1()

    stylesheet.add(ParagraphStyle(name='Normal',
                                  fontName=stdFont,
                                  fontSize=10,
                                  leading=12)
                   )

    stylesheet.add(ParagraphStyle(name='BodyText',
                                  parent=stylesheet['Normal'],
                                  spaceBefore=6)
                   )
    
    stylesheet.add(ParagraphStyle(name='Footer',
                                  parent=stylesheet['Normal'],
                                  backColor='#EFEFEF',
                                  alignment=TA_CENTER)
                   )
                   
    stylesheet.add(ParagraphStyle(name='Attribution',
                                  parent=stylesheet['BodyText'],
                                  alignment=TA_RIGHT)
                   )
                   
    stylesheet.add(ParagraphStyle(name='FieldName',
                                  parent=stylesheet['BodyText'],
                                  alignment=TA_RIGHT,
                                  fontName=stdBold,
                                  )
                   )
                   
    stylesheet.add(ParagraphStyle(name='Rubric',
                                  parent=stylesheet['BodyText'],
                                  textColor=colors.darkred,
                                  alignment=TA_CENTER)
                   )
                   
    stylesheet.add(ParagraphStyle(name='Italic',
                                  parent=stylesheet['BodyText'],
                                  fontName = stdItalic)
                   )
    
    stylesheet.add(ParagraphStyle(name='Title',
                                  parent=stylesheet['Normal'],
                                  fontName = stdBold,
                                  fontSize=18,
                                  leading=22,
                                  alignment=TA_CENTER,
                                  spaceAfter=6),
                   alias='title')
    stylesheet.add(ParagraphStyle(name='Subtitle',
                                  parent=stylesheet['Title'],
                                  fontSize=14),
                   alias='subtitle')

    stylesheet.add(ParagraphStyle(name='Heading1',
                                  parent=stylesheet['Normal'],
                                  fontName = stdBold,
                                  fontSize=18,
                                  leading=22,
                                  keepWithNext=True,
                                  spaceAfter=6),
                   alias='h1')


    stylesheet.add(ParagraphStyle(name='Heading2',
                                  parent=stylesheet['Normal'],
                                  fontName = stdBold,
                                  fontSize=14,
                                  leading=18,
                                  spaceBefore=12,
                                  keepWithNext=True,
                                  spaceAfter=6),
                   alias='h2')

    stylesheet.add(ParagraphStyle(name='Heading3',
                                  parent=stylesheet['Normal'],
                                  fontName = stdBoldItalic,
                                  fontSize=12,
                                  leading=14,
                                  spaceBefore=12,
                                  keepWithNext=True,
                                  spaceAfter=6),
                   alias='h3')
    
    stylesheet.add(ParagraphStyle(name='Heading4',
                                  parent=stylesheet['Normal'],
                                  fontName = stdBoldItalic,
                                  fontSize=12,
                                  leading=14,
                                  spaceBefore=12,
                                  keepWithNext=True,
                                  spaceAfter=6),
                   alias='h4')

    stylesheet.add(ParagraphStyle(name='Bullet',
                                  parent=stylesheet['Normal'],
                                  firstLineIndent=0,
                                  spaceBefore=3),
                   alias='bu')

    stylesheet.add(ParagraphStyle(name='Definition',
                                  parent=stylesheet['Normal'],
                                  firstLineIndent=0,
                                  leftIndent=36,
                                  bulletIndent=0,
                                  spaceBefore=6,
                                  fontName=stdBold),
                   alias='df')

    stylesheet.add(ParagraphStyle(name='Code',
                                  parent=stylesheet['Normal'],
                                  fontName=stdMono,
                                  fontSize=8,
                                  leading=8.8,
                                  firstLineIndent=0,
                                  leftIndent=36))


    return stylesheet



# Some table styles used for pieces of the document

tstyles={}

# Used for regular tables

tstyleNorm = [ ('VALIGN',(0,0),(-1,-1),'TOP'),
                               ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                               ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                             ]
                             
# Header row in tables

tstyleHead = ('BACKGROUND',(0,0),(-1,0),colors.yellow)
tstyles['Normal']=TableStyle(tstyleNorm)

# Used for field lists

tstyles['Field']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                              ('ALIGNMENT',(0,0),(1,-1),'RIGHT'),
                            ])
fieldlist_lwidth=3*cm

# Used for lists

tstyles['List']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                             ('ALIGNMENT',(0,0),(1,-1),'RIGHT'),
                           ])
list_lwidth=.6*cm
                           

# Used for endnotes

tstyles['Endnote']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                                ('ALIGNMENT',(0,0),(1,-1),'RIGHT'),
                              ])
# Left column of the endnote. The content of the note takes the rest of
# the available space
endnote_lwidth=2*cm

# Used for sidebars

tstyles['Sidebar']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                             ('BACKGROUND',(0,0),(-1,-1),colors.lightyellow),
                           ])
