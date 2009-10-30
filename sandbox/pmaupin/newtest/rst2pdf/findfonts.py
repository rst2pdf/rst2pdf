#!/usr/bin/env python
# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

"""
Scan a list of folders and find all .afm files,
then create rst2pdf-ready font-aliases.
"""

import os
import sys

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont, TTFError
from reportlab.lib.fonts import addMapping

from log import log

flist = []
afmList = []
pfbList = {}

# Aliases defined by GhostScript, so if you use Palatino or whatever you
# may get **something**. They are family name aliases.
Alias = {
    'ITC Bookman': 'URW Bookman L',
    'ITC Avant Garde Gothic': 'URW Gothic L',
    'Palatino': 'URW Palladio L',
    'New Century Schoolbook': 'Century Schoolbook L',
    'ITC Zapf Chancery': 'URW Chancery L'}

# Standard PDF fonts, so no need to embed them
Ignored = ['Times', 'ITC Zapf Dingbats', 'Symbol', 'Helvetica', 'Courier']


fonts = {}
families = {}
fontMappings = {}


def loadFonts():
    """Given a font name, returns the actual font files.

    If the font name is not valid, it will treat it as a font family name,
    and return the value of searching for the regular font of said family.

    """
    if not afmList or not pfbList:
        # Find all ".afm" and ".pfb" files files
        def findFontFiles(_, folder, names):
            for f in os.listdir(folder):
                if f.lower().endswith('.afm'):
                    afmList.append(os.path.join(folder, f))
                if f.lower().endswith('.pfb'):
                    pfbList[f[:-4]] = os.path.join(folder, f)

        for folder in flist:
            os.path.walk(folder, findFontFiles, None)

        # Now we have full afm and pbf lists, process the
        # afm list to figure out family name weight and if
        # it's italic or not, as well as where the
        # matching pfb file is

        for afm in afmList:
            family = None
            fontName = None
            italic = False
            bold = False
            for line in open(afm, 'r'):
                line = line.strip()
                if line.startswith('StartCharMetrics'):
                    break
                elif line.startswith('FamilyName'):
                    family = ' '.join(line.split(' ')[1:])
                elif line.startswith('FontName'):
                    fontName = line.split(' ')[1]
                # TODO: find a way to alias the fullname to this font
                # so you can use names like "Bitstream Charter Italic"
                elif line.startswith('FullName'):
                    fullName = line.split(' ')[1]
                elif line.startswith('Weight'):
                    w = line.split(' ')[1]
                    if w == 'Bold':
                        bold = True
                elif line.startswith('ItalicAngle'):
                    if line.split(' ')[1] != '0.0':
                        italic = True

            baseName = os.path.basename(afm)[:-4]
            if family in Ignored:
                continue
            if family in Alias:
                continue
            if baseName not in pfbList:
                log.info("afm file without matching pfb file: %s"% baseName)
                continue

            # So now we have a font we know we can embed.
            fonts[fontName] = (afm, pfbList[baseName], family)

            # And we can try to build/fill the family mapping
            if family not in families:
                families[family] = [fontName, fontName, fontName, fontName]
            if bold and italic:
                families[family][3] = fontName
            elif bold:
                families[family][1] = fontName
            elif italic:
                families[family][2] = fontName
            # FIXME: what happens if there are Demi and Medium
            # weights? We get a random one.
            else:
                families[family][0] = fontName

def findFont(fname):
    loadFonts()
    # So now we are sure we know the families and font
    # names. Well, return some data!
    if fname in fonts:
        font = fonts[fname]
    else:
        if fname in Alias:
            fname = Alias[fname]
        if fname in families:
            font = fonts[families[fname][0]]
        else:
            return None
    return font


def findTTFont(fname):

    def get_family(query):
        data = os.popen("fc-match \"%s\""%query, "r").read()
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            fname, family, _, variant = line.split('"')[:4]
            family = family.replace('"', '')
            if family:
                return family
        return None

    def get_fname(query):
        data = os.popen("fc-match -v \"%s\""%query, "r").read()
        for line in data.splitlines():
            line = line.strip()
            if line.startswith("file: "):
                return line.split('"')[1]
        return None

    def get_variants(family):
        variants = [
            get_fname(family + ":style=Roman"),
            get_fname(family + ":style=Bold"),
            get_fname(family + ":style=Oblique"),
            get_fname(family + ":style=Bold Oblique")]
        if variants[1] == variants[0]:
            variants[1] = get_fname(family + ":style=Italic")
        if variants[3] == variants[0]:
            variants[3] = get_fname(family + ":style=Bold Italic")
        if variants[0].endswith('.pfb') or variants[0].endswith('.gz'):
            return None
        return variants

    family = get_family(fname)
    if not family:
        log.error("Unknown font: %s", fname)
        return None
    return get_variants(family)


def autoEmbed(fname):
    """Given a font name, does a best-effort of embedding
    said font and its variants.

    Returns a list of the font names it registered with ReportLab.

    """
    log.info('Trying to embed %s'%fname)
    fontList = []
    f = findFont(fname)
    if f: # It's a Type 1 font, and we have it
        family = families[f[2]]

        # Register the whole family of faces
        faces = [pdfmetrics.EmbeddedType1Face(*fonts[fn][:2]) for fn in family]
        for face in faces:
            pdfmetrics.registerTypeFace(face)

        for face, name in zip(faces, family):
            fontList.append(name)
            font = pdfmetrics.Font(face, name, "WinAnsiEncoding")
            log.info('Registering font: %s from %s'%\
                        (face,name))
            pdfmetrics.registerFont(font)

        # Map the variants
        regular, italic, bold, bolditalic = family
        addMapping(fname, 0, 0, regular)
        addMapping(fname, 0, 1, italic)
        addMapping(fname, 1, 0, bold)
        addMapping(fname, 1, 1, bolditalic)
        addMapping(regular, 0, 0, regular)
        addMapping(regular, 0, 1, italic)
        addMapping(regular, 1, 0, bold)
        addMapping(regular, 1, 1, bolditalic)
        log.info('Embedding as %s'%fontList)
        return fontList

    variants = findTTFont(fname)
    # It is a TT Font and we found it using fc-match (or found *something*)
    if variants:
        for variant in variants:
            vname = os.path.basename(variant)[:-4]
            try:
                if vname not in pdfmetrics._fonts:
                    _font=TTFont(vname, variant, validate = 1)
                    log.info('Registering font: %s from %s'%\
                            (vname,variant))
                    pdfmetrics.registerFont(_font)
            except TTFError:
                log.error('Error registering font: %s from %s'%(vname,variant))
            else:
                fontList.append(vname)
        regular, bold, italic, bolditalic = [
            os.path.basename(variant)[:-4] for variant in variants]
        addMapping(regular, 0, 0, regular)
        addMapping(regular, 0, 1, italic)
        addMapping(regular, 1, 0, bold)
        addMapping(regular, 1, 1, bolditalic)
        log.info('Embedding via findTTFont as %s'%fontList)
    return fontList


def guessFont(fname):
    """Given a font name (like Tahoma-BoldOblique) guess what it means.

    Returns (family, x) where x is
        0: regular
        1: italic
        2: bold
        3: bolditalic

    """
    if '-' not in fname:
        return fname, 0
    italic = 0
    bold = 0
    family, mod = fname.split('-')
    mod = mod.lower()
    if "oblique" in mod or "italic" in mod:
        italic = 1
    if "bold" in mod or "black" in mod:
        bold = 1
    return family, bold + 2*italic


def main():
    global flist
    if len(sys.argv) != 2:
        print "Usage: findfont fontName"
        sys.exit(1)
    flist = [".", "/usr/share/fonts", "/usr/share/texmf-dist/fonts"]
    f = findFont(sys.argv[1])
    if not f:
        f = findTTFont(sys.argv[1])
    if f:
        print f
    else:
        fn, pos = guessFont(sys.argv[1])
        f = findFont(fn)
        if not f:
            f = findTTFont(fn)
        if f:
            print f
        else:
            print "Unknown font %s" % sys.argv[1]


if __name__ == "__main__":
    main()
