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


import os,sys

def _log(msg):
  sys.stderr.write('%s\n'%str(msg))
  sys.stderr.flush()

try:
  from wordaxe.rl.paragraph import Paragraph
  from wordaxe.rl.styles import ParagraphStyle,getSampleStyleSheet
except:
  _log("No hyphenation support, install wordaxe")




# Set these, and then **maybe** think of setting the stylesheets below
# if you want finer control

stdFont       = 'Helvetica'
stdBold       = 'Helvetica-Bold'
stdItalic     = 'Helvetica-Oblique'
stdBoldItalic = 'Helvetica-BoldOblique'
stdMono       = 'Courier'


TTFSearchPath=[os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fonts'),'.']

def findFont(fn):
  if not os.path.isabs(fn):
    for D in TTFSearchPath:
      tfn = os.path.join(D,fn)
      if os.path.isfile(tfn):
        return str(tfn)
    return str(fn)


def getStyleSheet(fname):
    """Returns a stylesheet object"""
    stylesheet = StyleSheet1()

    from simplejson import loads

    data=loads(open(fname).read())

    styles=data['styles']
    fonts=data['fontsAlias']
    embedded=data['embeddedFonts']

    for font in embedded:
      # Each "font" is a list of four files, which will be used for
      # regular / bold / italic / bold+italic versions of the font.
      # If your font doesn't have one of them, just repeat the regular
      # font.

      # Example, using the Tuffy font from http://tulrich.com/fonts/
      # "embeddedFonts" : [
      #                    ["Tuffy.ttf","Tuffy_Bold.ttf","Tuffy_Italic.ttf","Tuffy_Bold_Italic.ttf"]
      #                   ],

      # The fonts will be registered with the file name, minus the extension.

      for variant in font:
        pdfmetrics.registerFont(TTFont(str(variant.split('.')[0]), findFont(variant)))

      # And map them all together
      regular,bold,italic,bolditalic = [ variant.split('.')[0] for variant in font ]
      addMapping(regular,0,0,regular)
      addMapping(regular,0,1,italic)
      addMapping(regular,1,0,bold)
      addMapping(regular,1,1,bolditalic)

    while True:
      for [skey,style] in data['styles']:
	sdict={}
	if 'parent' in style:
	  if not style['parent']:
	    del style['parent']
	  else:
	    style['parent']=stylesheet[style['parent']]
	for key in style:

	  # Handle font aliases
	  if key in ['fontName','bulletFontName'] and style[key] in fonts:
	    style[key]=fonts[style[key]]

	  # Handle color references by name
	  if key in ['backColor','textColor'] and style[key] in colors.__dict__:
	    style[key]=colors.__dict__[style[key]]
	  
	  # Handle alignment constants
	  if key == 'alignment':
	    style[key]={'TA_LEFT':0, 'TA_CENTER':1, 'TA_CENTRE':1, 'TA_RIGHT':2, 'TA_JUSTIFY':4}[style[key]]
	  
	  # Make keys str instead of unicode (required by reportlab)
	  sdict[str(key)]=style[key]
	sdict['name']=skey
	stylesheet.add(ParagraphStyle(**sdict))
      else:
	break

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
tstyles['normal']=TableStyle(tstyleNorm)

# Used for field lists

tstyles['field']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                              ('ALIGNMENT',(0,0),(1,-1),'RIGHT'),
                            ])
fieldlist_lwidth=3*cm

# Used for endnotes

tstyles['endnote']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                                ('ALIGNMENT',(0,0),(1,-1),'RIGHT'),
                              ])
# Left column of the endnote. The content of the note takes the rest of
# the available space
endnote_lwidth=2*cm

# Used for sidebars

tstyles['sidebar']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                             ('BACKGROUND',(0,0),(-1,-1),colors.lightyellow),
                           ])
