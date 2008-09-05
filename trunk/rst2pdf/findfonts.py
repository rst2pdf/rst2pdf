#!/usr/bin/env python

'''Scan a list of folders and find all .afm files, then create rst2pdf-ready font-aliases.'''

import os,sys
from log import log

flist=[]
afmList=[]
pfbList={}

# Aliases defined by GhostScript, so if you use Palatino or whatever you
# may get **something**. They are family name aliases.
Alias = {
    'ITC Bookman'            : 'URW Bookman L',
    'ITC Avant Garde Gothic' : 'URW Gothic L',
    'Palatino'               : 'URW Palladio L',
    'New Century Schoolbook' : 'Century Schoolbook L',
    'ITC Zapf Chancery'      : 'URW Chancery L'
    }

# Standard PDF fonts, so no need to embed them
Ignored = ['Times', 'ITC Zapf Dingbats', 'Symbol', 'Helvetica', 'Courier']



fonts={}
families={}
fontMappings={}


def loadFonts():
    '''Given a font name, returns the actual font files. If the font name is not valid, it will treat it as a
    font family name, and return the value of searching for the regular font of said family.'''    
    if not afmList or not pfbList:
        # Find all ".afm" and ".pfb" files files
        def findFontFiles(_,folder,names):
            for f in os.listdir(folder):
                if f.lower().endswith('.afm'):
                    afmList.append(os.path.join(folder,f))
                if f.lower().endswith('.pfb'):
                    pfbList[f[:-4]]=os.path.join(folder,f)

        for folder in flist:
            os.path.walk(folder,findFontFiles,None)

        # Now we have full afm and pbf lists, process the afm list to figure out
        # family name weight and if it's italic or not, as well as where the
        # matching pfb file is

        for afm in afmList:
            family=None
            fontName=None
            italic=False
            bold=False
            pfb=None
            for line in open(afm,'r'):
                line=line.strip()
                if line.startswith('StartCharMetrics'):
                    break
                elif line.startswith('FamilyName'):
                    family=' '.join(line.split(' ')[1:])
                elif line.startswith('FontName'):
                    fontName=line.split(' ')[1]
                elif line.startswith('Weight'):
                    w=line.split(' ')[1]
                    if w=='Bold':
                        bold=True
                elif line.startswith('ItalicAngle'):
                    if line.split(' ')[1]<>'0.0':
                        italic=True

            baseName=os.path.basename(afm)[:-4]
            if family in Ignored:
                continue
            if family in Alias:
                continue
            if baseName not in pfbList:
                #print "Warning: afm file without matching pfb file: %s"%baseName
                continue

            # So now we have a font we knopw we can embed.
            fonts[fontName]=(afm,pfbList[baseName],family)

            # And we can try to build/fill the family mapping
            if family not in families:
                families[family]=[fontName,fontName,fontName,fontName]
            if bold and italic: families[family][3]=fontName
            elif bold: families[family][2]=fontName
            elif italic: families[family][1]=fontName
            # FIXME: what happens if there are Demi and Medium weights? We get a random one.
            else: families[family][0]=fontName

def findFont(fname):
    loadFonts()
    # So now we are sure we know the families and font names. Well, return some data!
    if fname in fonts:
        font=fonts[fname]
    if fname in Alias:
        fname=Alias[fname]
    if fname in families:
        font=fonts[families[fname][0]]
    else:
        log.warning("Unknown font %s"%fname)
        return None
    return font
        
def main():
    if len(sys.argv)<>2:
        print "Usage: findfont fontName"
        sys.exit(1)
    print findFont(sys.argv[1])


if __name__ == "__main__":
    main()
