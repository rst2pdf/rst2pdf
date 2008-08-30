# -*- coding: utf-8 -*-
#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

import os
import sys
import re
from reportlab.platypus import *
import reportlab.lib.colors as colors
import reportlab.lib.units as units
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.lib.styles import *
from reportlab.lib.enums import *
from reportlab.pdfbase import pdfmetrics
import reportlab.lib.pagesizes as pagesizes
from utils import log
from simplejson import loads

try:
    from wordaxe.rl.paragraph import Paragraph
    from wordaxe.rl.styles import ParagraphStyle,getSampleStyleSheet
except:
    log.warning("No hyphenation support, install wordaxe")


class StyleSheet(object):
    '''Class to handle a collection of stylesheets'''
    def __init__(self,flist):
        log.info('Using stylesheets: %s'%','.join(flist))
        '''flist is a list of stylesheet filenames.They will
        be loaded and merged in order'''
        self.TTFSearchPath=[os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fonts'),'.']

        # Page width, height
        self.pw=0
        self.ph=0

        # Page size [w,h]
        self.ps=None

        # Margins (top,bottom,left,right,gutter)
        self.tm=0
        self.bm=0
        self.lm=0
        self.rm=0
        self.gm=0

        #text width
        self.tw=0

        self.languages=[]
        ssdata=[]
        # First parse all files and store the results
        for fname in flist:
            try:
                ssdata.append(loads(open(fname).read()))
            except ValueError,e: # Error parsing the JSON data
                log.error('Error parsing stylesheet "%s": %s'%(fname,str(e)))
                sys.exit(1)
            except IOError,e: #Error opening the ssheet
                log.error('Error opening stylesheet "%s": %s'%(fname,str(e)))
                sys.exit(1)

        # Get pageSetup data from all stylessheets in order:
        for data,ssname in zip(ssdata,flist):
            page=data.get('pageSetup',{})
            if page:
                if page.get('size',None): # A standard size
                    if page['size'] in pagesizes.__dict__:
                        self.ps=pagesizes.__dict__[page['size']]
                    else:
                        log.critical('Unknown page size %s in stylesheet %s' % (page['size'],ssname))
                        sys.exit(1)
                else: #A custom size
                    # The sizes are expressed in some unit.
                    # For example, 2cm is 2 centimeters, and we need
                    # to do 2*cm (cm comes from reportlab.lib.units)
                    self.ps=[self.adjustUnits(page['width']),self.adjustUnits(page['height'])]
                self.pw,self.ph=self.ps
                if 'margin-left' in page:
                    self.lm=self.adjustUnits(page['margin-left'])
                if 'margin-right' in page:
                    self.rm=self.adjustUnits(page['margin-right'])
                if 'margin-top' in page:
                    self.tm=self.adjustUnits(page['margin-top'])
                if 'margin-bottom' in page:
                    self.bm=self.adjustUnits(page['margin-bottom'])
                if 'margin-gutter' in page:
                    self.gm=self.adjustUnits(page['margin-gutter'])

                # tw is the text width.
                # We need it to calculate header-footer height
                # and compress literal blocks.
                self.tw=self.pw-self.lm-self.rm-self.gm

        # Get font aliases from all stylesheets in order
        self.fonts={}
        for data,ssname in zip(ssdata,flist):
            self.fonts.update(data.get('fontsAlias',{}))
            embedded=data.get('embeddedFonts',[])

            for font in embedded:
                try:
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
                except:
                    try:
                        fname=font[0].split('.')[0]
                        log.error("Error processing font %s, registering as Helvetica alias",fname)
                        fonts[fname]='Helvetica'
                    except:
                        log.error("Error processing font %s",fname)
                        sys.exit(1)

        # Get styles from all stylesheets in order
        self.stylesheet = {}
        self.styles=[]
        self.linkColor = 'navy'
        for data,ssname in zip(ssdata,flist):
            self.linkColor=data.get('linkColor') or self.linkColor
            styles=data.get('styles',{})
            for [skey,style] in styles:
                sdict={}
                # FIXME: this is done completely backwards
                for key in style:

                    # Handle font aliases
                    if (key == 'fontName' or key.endswith('FontName')) and style[key] in self.fonts:
                        style[key]=self.fonts[style[key]]

                    # Handle color references by name
                    elif key == 'color' or key.endswith('Color') and style[key]:
                        if style[key] in colors.__dict__:
                            style[key]=colors.__dict__[style[key]]
                        else: # Hopefully, a hex color:
                            c=style[key]
                            r=int(c[1:3],16)
                            g=int(c[3:5],16)
                            b=int(c[5:7],16)
                            style[key]=colors.Color(r,g,b)

                    # Handle alignment constants
                    elif key == 'alignment':
                        style[key]={'TA_LEFT':0, 'TA_CENTER':1, 'TA_CENTRE':1, 'TA_RIGHT':2, 'TA_JUSTIFY':4}[style[key]]

                    elif key == 'language':
                        if not style[key] in self.languages:
                            self.languages.append(style[key])
                    # Make keys str instead of unicode (required by reportlab)
                    sdict[str(key)]=style[key]
                    sdict['name']=skey
                # If the style already exists, update it
                if skey in self.stylesheet:
                    self.stylesheet[skey].update(sdict)
                else: # New style
                    self.stylesheet[skey]=sdict
                    self.styles.append(sdict)
        # And create  reportlabs stylesheet
        self.StyleSheet=StyleSheet1()
        for s in self.styles:
            if 'parent' in s:
                if s['parent'] is None:
                    if s['name'] <> 'base':
                        s['parent']=self.StyleSheet['base']
                    else:
                        del(s['parent'])
                else:
                    s['parent']=self.StyleSheet[s['parent']]
            else:
                if s['name'] <> 'base':
                    s['parent']=self.StyleSheet['base']
            self.StyleSheet.add(ParagraphStyle(**s))
    def __getitem__(self,key):
        return self.StyleSheet[key]

    def findFont(fn):
        '''Given a font file name, searches for it in TTFSearchPath
        and returns the real file name'''
        if not os.path.isabs(fn):
            for D in self.TTFSearchPath:
                tfn = os.path.join(D,fn)
                if os.path.isfile(tfn):
                    return str(tfn)
        return str(fn)

    def adjustUnits(self,v,total=None):
        '''Takes something like 2cm and returns 2*cm.
        If you use % as a unit, it returns the percentage
        of "total".

        If total is not given, returns a percentage of the page
        width. However, if you get to that stage, you are
        doing it wrong.

        Example::

                >>> adjustUnits('50%',200)
                100
        '''

        if total is None:
            total=self.pw

        _,n,u=re.split('(-?[0-9\.]*)',v)
        if not u:
            return float(n) # assume points
        if u in units.__dict__:
            return float(n)*units.__dict__[u]
        else:
            if u=='%':
                return float(n)*total/100
            log.error('Unknown unit "%s"' % u)
        return float(n)


# Some table styles used for pieces of the document

tstyles={}

# Used for regular tables

tstyleNorm = [ ('VALIGN',(0,0),(-1,-1),'TOP'),
               ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
               ('BOX', (0,0), (-1,-1), 0.25, colors.black),
             ]

# Header row in tables

def tstyleHead(rows=1):
    return ('BACKGROUND',(0,0),(-1,rows-1),colors.yellow)

tstyles['normal']=TableStyle(tstyleNorm)

# Used for field lists

tstyles['field']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                              ('ALIGNMENT',(0,0),(1,-1),'RIGHT'),
                            ])
fieldlist_lwidth=3*units.cm

# Used for endnotes

tstyles['endnote']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                                ('ALIGNMENT',(0,0),(1,-1),'RIGHT'),
                              ])
# Left column of the endnote. The content of the note takes the rest of
# the available space
endnote_lwidth=2*units.cm

# Used for sidebars

tstyles['sidebar']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                             ('BACKGROUND',(0,0),(-1,-1),colors.lightyellow),
                           ])


tstyles['bullet']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                             ])
