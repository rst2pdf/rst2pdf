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
    md5dir = os.path.join(rootdir, 'md5')

    if not os.path.exists(runfile):
        raise SystemExit('Use bootstrap.py and buildout to create executable')

    ppath = os.environ.get('PYTHONPATH')
    ppath = ppath is None and rootdir or '%s:%s' % (ppath, rootdir)
    os.environ['PYTHONPATH'] = ppath

def run_single_textfile(fname):
    iprefix = os.path.splitext(fname)[0]
    basename = os.path.basename(iprefix)
    oprefix = os.path.join(PathInfo.outdir, basename)
    mprefix = os.path.join(PathInfo.md5dir, basename)
    style = iprefix + '.style'
    outpdf = oprefix + '.pdf'
    outtext = oprefix + '.log'
    md5file = mprefix + '.json'

    args = [PathInfo.runfile, '-v', fname]
    if os.path.exists(style):
        args.extend(('-s', style))
    args.extend(('-o', outpdf))
    result = textexec(args)
    result.append('\n')
    outf = open(outtext, 'wb')
    outf.write('\n'.join(result))
    outf.close()

def run_textfiles(textfiles=None):
    if not textfiles:
        textfiles = glob.glob(os.path.join(PathInfo.inpdir, '*.txt'))
        textfiles.sort()
    for fname in textfiles:
        run_single_textfile(fname)

if __name__ == '__main__':
    import sys
    run_textfiles(sys.argv[1:])
