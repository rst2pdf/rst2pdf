# -*- coding: utf-8 -*-

# An extension module for rst2pdf
# Copyright 2010, Patrick Maupin
# See LICENSE.txt for licensing terms

'''
preprocess is a rst2pdf extension module (invoked by -e preprocess
on the rst2pdf command line.

It preprocesses the source text file before handing it to docutils.

This module serves two purposes:

1) It demonstrates the technique and can be a starting point for similar
   user-written processing modules; and

2) It provides a simplified syntax for documents which are targeted only
   at rst2pdf, rather than docutils in general.

The design goal of "base rst2pdf" is to be completely compatible with
docutils, such that a file which works as a PDF can also work as HTML,
etc.

Unfortunately, base docutils is a slow-moving target, and does not
make this easy.  For example, SVG images do not work properly with
the HTML backend unless you install a patch, and docutils has no
concept of page breaks or additional vertical space (other than
the <hr>).

So, while it would be nice to have documents that render perfectly
with any backend, this goal is hard to achieve for some documents,
and once you are restricted to a particular transformation type,
then you might as well have a slightly nicer syntax for your source
document.

-----------------------------------------------------------------

Preprocessor extensions:

All current extensions except style occupy a single line in the
source file.

``.. include::``

    Processes the include file as well.

``.. page::``       

    Is translated into a raw PageBreak

``.. space::``      

    Is translated into a raw Spacer.  If only one number given, is
    used for vertical

``.. style::``

    Allows you to create in-line stylesheets.
    (If you wish them to be in YAML format, you must give
    -e yaml before -e preprocess on the command line.)

``.. widths::`` 

    creates a new table style (based on table or the first
    non-numeric token) and creates a class using that style for
    the next table.  Allows you to set the widths for the table,
    using percentages.

``SingleWordAtLeftColumn``   

    If this is surrounded by blank lines, the singleword
    style is applied to the word.  This is a workaround
    for the broken interaction between docutils subtitles
    and bibliographic metadata.  Who wants a subtitle
    inside the TOC?

-----------------------------------------------------------------

Preprocessor operation:

The preprocessor generates a file that has the same name as the source
file, with .build_temp. embedded in the name, and then passes that
file to the restructured text parser.

This file is left on the disk after operation, because any error
messages from docutils will refer to line numbers in it, rather than
in the original source.

'''

import os
import re

from rst2pdf.rson import loads as rson_loads

from rst2pdf.log import log

class DummyFile(str):
    def read(self):
        return self

class Preprocess(object):
    blankline  = r'^([ \t]*\n)'
    singleword = r'^([A-Za-z]+[ \t]*\n)(?=[ \t]*\n)'
    keywords = set('page space widths style include'.split())
    comment = r'^(\.\.[ \t]+(?:%s)\:\:.*\n)' % '|'.join(keywords)
    expression = '(?:%s)' % '|'.join([blankline, singleword, comment])
    splitter = re.compile(expression, re.MULTILINE).split

    def __init__(self, sourcef, incfile=False):
        name = sourcef.name
        source = sourcef.read().replace('\r\n', '\n').replace('\r', '\n')

        if incfile:
            try:
                self.styles = rson_loads(source)
            except:
                pass
            else:
                self.styles['styles'] = dict(self.styles['styles'])
                self.changed = True
                self.keep = False
                return

        self.sourcef = DummyFile(source)
        self.sourcef.name = name
        self.source = source = [x for x in self.splitter(source) if x]
        self.result = result = []
        self.styles = {}
        self.widthcount = 0
        self.changed = False

        source.reverse()
        isblank = False
        while source:
            wasblank = isblank
            isblank = False
            chunk = source.pop()
            result.append(chunk)

            # Only process single lines
            if not chunk.endswith('\n'):
                continue
            result[-1] = chunk[:-1]
            if chunk.index('\n') != len(chunk)-1:
                continue
            tokens = chunk.split()
            isblank = not tokens
            if len(tokens) >= 2 and tokens[0] == '..' and tokens[1].endswith('::'):
                keyword = tokens[1][:-2]
                if keyword not in self.keywords:
                    continue
                chunk = chunk.split('::', 1)[1]
            elif wasblank and len(tokens) == 1 and chunk[0].isalpha() and tokens[0].isalpha():
                keyword = 'single'
                chunk = tokens[0]
            else:
                continue

            result.pop()
            getattr(self, 'handle_'+keyword)(chunk.strip())

        if self.changed:
            result.append('')
            result = DummyFile('\n'.join(result))
            result.name = name + '.build_temp'
            self.keep = keep = len(result.strip())
            if keep:
                f = open(result.name, 'wb')
                f.write(result)
                f.close()
            self.result = result
        else:
            self.result = self.sourcef

    def handle_include(self, fname):
        for prefix in ('', os.path.dirname(self.sourcef.name)):
            try:
                f = open(os.path.join(prefix, fname), 'rb')
            except IOError:
                continue
            else:
                break
        else:
            log.error("Could not find include file %s", fname)
            self.changed = True
            return

        inc = Preprocess(f, True)
        self.styles.update(inc.styles)
        if inc.changed:
            self.changed = True
            if not inc.keep:
                return
            fname = inc.result.fname
        self.result.extend(['', '', '.. include:: ' + fname, ''])

    def handle_single(self, word):
        self.changed = True
        self.result.extend(['', '', '.. class:: singleword', '', word, ''])

    def handle_page(self, chunk):
        self.changed = True
        self.result.extend(['', '', '.. raw:: pdf', '',
                    '    PageBreak ' + chunk, ''])

    def handle_space(self, chunk):
        self.changed = True
        if len(chunk.replace(',', ' ').split()) == 1:
            chunk = '0 ' + chunk
        self.result.extend(['', '', '.. raw:: pdf', '',
                    '    Spacer ' + chunk, ''])

    def handle_widths(self, chunk):
        self.changed = True
        chunk = chunk.replace(',', ' ').replace('%', ' ').split()
        if not chunk:
            log.error('no widths specified in .. widths ::')
            return
        parent = chunk[0][0].isalpha() and chunk.pop(0) or 'table'
        values = [float(x) for x in chunk]
        total = sum(values)
        values = [int(round(100 * x / total)) for x in values]
        while 1:
            total = sum(values)
            if total > 100:
                values[index(max(values))] -= 1
            elif total < 100:
                values[index(max(values))] += 1
            else:
                break

        values = ['%s%%' % x for x in values]
        self.widthcount += 1
        stylename = 'embeddedtablewidth%d' % self.widthcount
        self.styles.setdefault('styles', {})[stylename] = dict(parent=parent, colWidths=values)
        self.result.extend(['', '', '.. class:: ' + stylename, ''])

    def handle_style(self, chunk):
        self.changed = True
        if chunk:
            log.error(".. styles:: does not recognize string %s" % repr(chunk))
            return
        source = self.source
        data = source and source.pop().splitlines() or []
        data.reverse()
        mystyles = []
        while data:
            myline = data.pop().rstrip()
            if not myline:
                continue
            if myline.lstrip() == myline:
                data.append(myline)
                break
            mystyles.append(myline)
        data.reverse()
        data.append('')
        source.append('\n'.join(data))
        if not mystyles:
            log.error("Empty .. styles:: block found")
        indent = min(len(x) - len(x.lstrip()) for x in mystyles)
        mystyles = [x[indent:] for x in mystyles]
        mystyles.append('')
        mystyles = '\n'.join(mystyles)
        try:
            styles = rson_loads(mystyles)
            self.styles.setdefault('styles', {}).update(styles)
        except ValueError, e: # Error parsing the JSON data
                log.critical('Error parsing stylesheet "%s": %s'%\
                    (mystyles, str(e)))

class MyStyles(str):
    def __new__(cls, styles):
        self = str.__new__(cls, 'Embedded Preprocess Styles')
        self.data = styles
        return self
    def __call__(self):
        return self.data

def install(createpdf, options):
    data = Preprocess(options.infile)
    options.infile = data.result
    if data.styles:
        options.style.append(MyStyles(data.styles))
