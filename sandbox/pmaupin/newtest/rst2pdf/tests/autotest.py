#!/usr/bin/env python
# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

'''
Copyright (c) 2009 Pat Maupin

Automated testing for rst2pdf

'''
import os
import glob
from execmgr import textexec

class PathInfo(object):
    rootdir = os.path.realpath(os.path.dirname(__file__))
    runfile = os.path.abspath(os.path.join(rootdir, '..', '..', 'bin', 'rst2pdf'))
    inpdir = os.path.join(rootdir, 'input')
    outdir = os.path.join(rootdir, 'output')

    if not os.path.exists(outdir):
        os.mkdir(outdir)

    if not os.path.exists(runfile):
        raise SystemExit('Use bootstrap.py and buildout to create executable')

def run_single_textfile(fname):
    iprefix = os.path.splitext(fname)[0]
    oprefix = os.path.join(PathInfo.outdir, os.path.basename(iprefix))
    style = iprefix + '.style'
    outpdf = oprefix + '.pdf'
    outtext = oprefix + '.log'

    args = [PathInfo.runfile, '-v', fname]
    if os.path.exists(style):
        args.extend(('-s', style))
    args.extend(('-o', outpdf))
    #args.insert(0, './tryme.py')
    result = textexec(args)
    result.append('\n')
    outf = open(outtext, 'wb')
    outf.write('\n'.join(result))
    outf.close()

def run_textfiles():
    textfiles = glob.glob(os.path.join(PathInfo.inpdir, '*.txt'))
    textfiles.sort()
    for fname in textfiles:
        run_single_textfile(fname)

run_textfiles()
