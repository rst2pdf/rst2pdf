#!/usr/bin/env python
# -*- coding: utf-8 -*-

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.platypus.doctemplate import Indenter
from reportlab.platypus.flowables import *
from reportlab.platypus.xpreformatted import *
from reportlab.lib.styles import getSampleStyleSheet
from copy import copy

def go():
        Story=[]
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate("issue216.pdf")
        
        space=Spacer(0,0)
        
        knstyle=copy(styles['Normal'])
        heading1=Paragraph('Heading 1',knstyle)
        heading1.keepWithNext=True
        content= XPreformatted('This is the content\n'*120,styles['Normal'])
        
        Story=[space,heading1,content]
        doc.build(Story)

go()
