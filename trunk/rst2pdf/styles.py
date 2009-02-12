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
from log import log
from simplejson import loads
import docutils.nodes
import findfonts

try:
    from wordaxe.rl.paragraph import Paragraph
    from wordaxe.rl.styles import ParagraphStyle,getSampleStyleSheet
except:
    pass
    #log.warning("No hyphenation support, install wordaxe")

unit_separator = re.compile('(-?[0-9\.]*)')

class StyleSheet(object):
    '''Class to handle a collection of stylesheets'''
    def __init__(self,flist,fontPath=[],stylePath=None):
        log.info('Using stylesheets: %s'%','.join(flist))
        '''flist is a list of stylesheet filenames.They will
        be loaded and merged in order'''
        self.FontSearchPath=fontPath+['.',os.path.join(os.path.abspath(os.path.dirname(__file__)), 'fonts')]
        if stylePath is None:
            stylePath=['.',os.path.join(os.path.abspath(os.path.dirname(__file__)), 'styles'),'~/.rst2pdf/styles']
        self.StyleSearchPath=map(os.path.expanduser,stylePath)

        findfonts.flist=self.FontSearchPath
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
            fname = self.findStyle(fname)
            try:
                ssdata.append(loads(open(fname).read()))
            except ValueError,e: # Error parsing the JSON data
                log.critical('Error parsing stylesheet "%s": %s'%(fname,str(e)))
                sys.exit(1)
            except IOError,e: #Error opening the ssheet
                log.critical('Error opening stylesheet "%s": %s'%(fname,str(e)))
                sys.exit(1)

        # Get pageSetup data from all stylessheets in order:
        self.ps=pagesizes.A4
        for data, ssname in zip(ssdata, flist):
            page=data.get('pageSetup', {})
            if page:
                if page.get('size', None): # A standard size
                    if page['size'] in pagesizes.__dict__:
                        self.ps=list(pagesizes.__dict__[page['size']])
                    else:
                        log.critical('Unknown page size %s in stylesheet %s' % (page['size'],ssname))
                        sys.exit(1)
                else: #A custom size
                    # The sizes are expressed in some unit.
                    # For example, 2cm is 2 centimeters, and we need
                    # to do 2*cm (cm comes from reportlab.lib.units)
                    if 'width' in page:
                        self.ps[0]=self.adjustUnits(page['width'])
                    if 'height' in page:
                        self.ps[1]=self.adjustUnits(page['height'])
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
                if 'firstTemplate' in page:
                    self.firstTemplate=page['firstTemplate']

                # tw is the text width.
                # We need it to calculate header-footer height
                # and compress literal blocks.
                self.tw=self.pw-self.lm-self.rm-self.gm

        # Get page templates from all stylesheets
        self.pageTemplates={}
        for data, ssname in zip(ssdata,flist):
            templates=data.get('pageTemplates',{})
            # templates is a dictionary of pageTemplates
            for key in templates:
                template=templates[key]
                # template is a dict.
                # template[´frames'] is a list of frames
                if key in self.pageTemplates:
                    self.pageTemplates[key].update(template)
                else:
                    self.pageTemplates[key]=template

        # Get font aliases from all stylesheets in order
        self.fontsAlias={}
        for data, ssname in zip(ssdata, flist):
            self.fontsAlias.update(data.get('fontsAlias',{}))

        embedded_fontnames = []
        self.embedded=[]
        # Embed all fonts indicated in all stylesheets
        for data, ssname in zip(ssdata, flist):
            embedded=data.get('embeddedFonts',[])

            for font in embedded:
                try:
                    if isinstance(font,unicode): # Just a font name, try to embed it
                        # See if we can find the font
                        fname,pos=findfonts.guessFont(font)
                        if font in embedded_fontnames:
                            pass
                        else:
                            fontList=findfonts.autoEmbed(font)
                            if fontList:
                                embedded_fontnames.append(font)
                        if not fontList:
                            if (fname, pos) in embedded_fontnames:
                                fontList=None
                            else:
                                fontList=findfonts.autoEmbed(fname)
                        if fontList is not None:
                            self.embedded+=fontList
                            # Maybe the font we got is not called the same as the one we gave
                            # so check that out
                            suff=["","-Oblique","-Bold","-BoldOblique"]
                            if not fontList[0].startswith(font):
                                # We need to create font aliases, and use them
                                for fname,aliasname in zip(fontList,[font+suffix for suffix in suff]):
                                    self.fontsAlias[aliasname]=fname
                        continue

                    # Each "font" is a list of four files, which will be used for
                    # regular / bold / italic / bold+italic versions of the font.
                    # If your font doesn't have one of them, just repeat the regular
                    # font.

                    # Example, using the Tuffy font from http://tulrich.com/fonts/
                    # "embeddedFonts" : [
                    #                    ["Tuffy.ttf","Tuffy_Bold.ttf","Tuffy_Italic.ttf","Tuffy_Bold_Italic.ttf"]
                    #                   ],

                    # The fonts will be registered with the file name, minus the extension.

                    if font[0].lower().endswith('.ttf'): # A True Type font
                        for variant in font:
                            pdfmetrics.registerFont(TTFont(str(variant.split('.')[0]), self.findFont(variant)))
                            self.embedded.append(str(variant.split('.')[0]))

                        # And map them all together
                        regular,bold,italic,bolditalic = [ variant.split('.')[0] for variant in font ]
                        addMapping(regular,0,0,regular)
                        addMapping(regular,0,1,italic)
                        addMapping(regular,1,0,bold)
                        addMapping(regular,1,1,bolditalic)
                    else: # A Type 1 font
                        # For type 1 fonts we require [FontName,regular,italic,bold,bolditalic]
                        # where each variant is a (pfbfile,afmfile) pair.
                        # For example, for the URW palladio from TeX:
                        # ["Palatino",("uplr8a.pfb","uplr8a.afm"),("uplri8a.pfb","uplri8a.afm"),("uplb8a.pfb","uplb8a.afm"),("uplbi8a.pfb","uplbi8a.afm")]
                        faceName=font[0]
                        regular=pdfmetrics.EmbeddedType1Face(*font[1])
                        italic=pdfmetrics.EmbeddedType1Face(*font[2])
                        bold=pdfmetrics.EmbeddedType1Face(*font[3])
                        bolditalic=pdfmetrics.EmbeddedType1Face(*font[4])

                except Exception, e:
                    try:
                        if isinstance(font, list):
                            fname=font[0]
                        else:
                            fname=font
                        log.error("Error processing font %s: %s", os.path.splitext(fname)[0],str(e))
                        log.error("Registering %s as Helvetica alias",fname)
                        self.fontsAlias[fname]='Helvetica'
                    except Exception,e:
                        log.critical("Error processing font %s: %s",fname,str(e))
                        sys.exit(1)

        # Go though all styles in all stylesheets and find all fontNames.
        # Then decide what to do with them
        for data, ssname in zip(ssdata, flist):
            styles = data.get('styles', {})
            for [skey, style] in styles:
                for key in style:
                    if key == 'fontName' or key.endswith('FontName'):
                        if style[key] in self.fontsAlias: # It´s an alias, replace it
                            style[key]=self.fontsAlias[style[key]]
                        if style[key] in self.embedded: # Embedded already, nothing to do
                            continue
                        if style[key] in ("Courier",
                                          "Courier-Bold",
                                          "Courier-BoldOblique",
                                          "Courier-Oblique",
                                          "Helvetica",
                                          "Helvetica-Bold",
                                          "Helvetica-BoldOblique",
                                          "Helvetica-Oblique",
                                          "Symbol",
                                          "Times-Bold",
                                          "Times-BoldItalic",
                                          "Times-Italic",
                                          "Times-Roman",
                                          "ZapfDingbats"): # Standard font, nothing to do
                            continue

                        # Now we need to do something
                        # See if we can find the font
                        fname,pos=findfonts.guessFont(style[key])

                        if style[key] in embedded_fontnames:
                            pass
                        else:
                            fontList=findfonts.autoEmbed(style[key])
                            if fontList:
                                embedded_fontnames.append(style[key])
                        if not fontList:
                            if (fname, pos) in embedded_fontnames:
                                fontList=None
                            else:
                                fontList=findfonts.autoEmbed(fname)
                            if fontList:
                                embedded_fontnames.append((fname, pos))
                        if fontList:
                            self.embedded+=fontList
                            # Maybe the font we got is not called the same as the one we gave
                            # so check that out
                            suff=["","-Oblique","-Bold","-BoldOblique"]
                            if not fontList[0].startswith(style[key]):
                                # We need to create font aliases, and use them
                                for fname,aliasname in zip(fontList,[style[key]+suffix for suffix in suff]):
                                    self.fontsAlias[aliasname]=fname
                                style[key]=self.fontsAlias[style[key]+suff[pos]]
                        else:
                            log.error("Unknown font: \"%s\", replacing with Helvetica",style[key])
                            style[key]="Helvetica"

        # Get styles from all stylesheets in order
        self.stylesheet = {}
        self.styles=[]
        self.linkColor = 'navy'
        for data, ssname in zip(ssdata, flist):
            self.linkColor = data.get('linkColor') or self.linkColor
            styles = data.get('styles', {})
            for [skey, style] in styles:
                sdict = {}
                # FIXME: this is done completely backwards
                for key in style:
                    # Handle color references by name
                    if key == 'color' or key.endswith('Color') and style[key]:
                        style[key]=formatColor(style[key])

                    # Handle alignment constants
                    elif key == 'alignment':
                        style[key]={'TA_LEFT':0, 'TA_CENTER':1, 'TA_CENTRE':1, 'TA_RIGHT':2, 'TA_JUSTIFY':4, 'DECIMAL':8}[style[key]]

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
        self.StyleSheet = StyleSheet1()
        for s in self.styles:
            if 'parent' in s:
                if s['parent'] is None:
                    if s['name'] != 'base':
                        s['parent'] = self.StyleSheet['base']
                    else:
                        del(s['parent'])
                else:
                    s['parent'] = self.StyleSheet[s['parent']]
            else:
                if s['name'] != 'base':
                    s['parent'] = self.StyleSheet['base']

            # If the style has no bulletFontName but it has a fontName, set it
            if ('bulletFontName' not in s) and ('fontName' in s):
                s['bulletFontName']=s['fontName']

            hasFS=True
            # Adjust fontsize units
            if 'fontSize' not in s:
                s['fontSize']=s['parent'].fontSize
                hasFS=False
            elif 'parent' in s:
                # This means you can set the fontSize to "2cm" or to "150%" which
                # will be calculated relative to the parent style
                s['fontSize']=self.adjustUnits(s['fontSize'],s['parent'].fontSize)
            else:
                # If s has no parent, it's base, which has an explicit point size
                # by default and % makes no sense, but guess it as % of 10pt
                s['fontSize']=self.adjustUnits(s['fontSize'],10)

            # If the leading is not set, but the size is, set it
            if 'leading' not in s and hasFS:
                s['leading']=1.2*s['fontSize']

            # If the bullet font size is not set, set it as fontSize
            if ('bulletFontSize' not in s) and ('fontSize' in s):
                s['bulletFontSize'] = s['fontSize']

            self.StyleSheet.add(ParagraphStyle(**s))

    def __getitem__(self,key):
        return self.StyleSheet[key]

    def findStyle(self,fn):
        '''Given a style filename, searches for it in StyleSearchPath
        and returns the real file name'''
        if not os.path.isabs(fn):
            for D in self.StyleSearchPath:
                tfn = os.path.join(D,fn)
                if os.path.isfile(tfn):
                    return str(tfn)
        return str(fn)

    def findFont(self,fn):
        '''Given a font filename, searches for it in FontSearchPath
        and returns the real file name'''
        if not os.path.isabs(fn):
            for D in self.FontSearchPath:
                tfn = os.path.join(D,fn)
                if os.path.isfile(tfn):
                    return str(tfn)
        return str(fn)

    def styleForNode(self,node):
        '''Returns the right default style for any kind of node.
        That usually means "bodytext", but for sidebars, for
        example, it's sidebar'''

        if isinstance(node,docutils.nodes.sidebar):
            return self['sidebar']
        return self['bodytext']

    def tstyleHead(self,rows=1):
        '''Returns a table style spec for a table header of `rows` based on the
        table-heading style from the stylesheet'''
        # This alignment thing is exactly backwards from the alignment for paragraphstyles
        alignment={0:'LEFT', 1:'CENTER', 1:'CENTRE', 2:'RIGHT', 4:'JUSTIFY',8:'DECIMAL'}[self['table-heading'].alignment]
        return [('BACKGROUND',(0,0),(-1,rows-1),self['table-heading'].backColor),
                ('ALIGN',(0,0),(-1,rows-1),alignment),
                ('TEXTCOLOR',(0,0),(-1,rows-1),self['table-heading'].textColor),
                ('FONT',(0,0),(-1,rows-1),self['table-heading'].fontName,
                                          self['table-heading'].fontSize,
                                          self['table-heading'].leading),
                ('VALIGN',(0,0),(-1,rows-1),self['table-heading'].valign)
               ]

    def tstyleBody(self,rows=1):
        '''Returns a table style spec for a table of any size based on the
        table style from the stylesheet'''
        return [("ROWBACKGROUNDS",(0,0),(-1,-1),
                [formatColor(c,numeric=False) for c in self['table'].rowBackgrounds]),
            ]

    def pStyleToTStyle(self,style,x,y):
        '''Given a reportlab paragraph style, returns a spec for a table style
           that adopts some of its features (example, background color)'''
        results=[]
        if style.backColor:
            results.append(('BACKGROUND',(x,y),(x,y),style.backColor))
        if style.borderWidth:
            bw=style.borderWidth
            del(style.__dict__['borderWidth'])
            if style.borderColor:
                bc=style.borderColor
                del(style.__dict__['borderColor'])
            else:
                bc=colors.black
            results.append(('BOX',(x,y),(x,y),bw,bc))
        return results

    def adjustUnits(self, v, total = None):
        if total is None:
            total = self.pw
        return adjustUnits(v,total)

def adjustUnits(v,total=None):
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

    v = str(v)
    _,n,u = re.split('(-?[0-9\.]*)',v)
    if not u:
        return float(n) # assume points
    if u in units.__dict__:
        return float(n) * units.__dict__[u]
    else:
        if u=='%':
            return float(n) * total/100
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


tstyles['normal']=TableStyle(tstyleNorm)

# Used for field lists

tstyles['field']=TableStyle([ ('VALIGN',(0,0),(-1,-1),'TOP'),
                              ('ALIGNMENT',(0,0),(1,-1),'RIGHT'),
                              ('TOPPADDING', (0,0), (-1,-1), 0),
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

def formatColor(value,numeric=True):
    '''Converts a color like "gray" or "0xf" or "ffff" to something
    reportlab will like'''
    if value in colors.__dict__:
        return colors.__dict__[value]
    else: # Hopefully, a hex color:
        c = value.strip()
        if c[0] == '#':
            c = c[1:]
        while len(c) < 6:
            c = '0'+c
        if numeric:
            r = int(c[:2],16)/255.
            g = int(c[2:4],16)/255.
            b = int(c[4:6],16)/255.
            return colors.Color(r,g,b)
        else:
            return str("#"+c)
