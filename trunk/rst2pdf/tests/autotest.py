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
import hashlib
from copy import copy
from optparse import OptionParser
from execmgr import textexec

class PathInfo(object):
    rootdir = os.path.realpath(os.path.dirname(__file__))
    bindir = os.path.abspath(os.path.join(rootdir, '..', '..', 'bin'))
    runfile = os.path.join(bindir, 'rst2pdf')
    inpdir = os.path.join(rootdir, 'input')
    outdir = os.path.join(rootdir, 'output')
    md5dir = os.path.join(rootdir, 'md5')

    if not os.path.exists(runfile):
        raise SystemExit('Use bootstrap.py and buildout to create executable')

    ppath = os.environ.get('PYTHONPATH')
    ppath = ppath is None and rootdir or '%s:%s' % (ppath, rootdir)
    os.environ['PYTHONPATH'] = ppath

    runcmd = [runfile]

    @classmethod
    def add_coverage(cls, keep=False):
        cls.runcmd[0:0] = [os.path.join(cls.bindir, 'real_coverage'), 'run', '-a']
        if not keep:
            fname = os.path.join(cls.rootdir, '.coverage')
            if os.path.exists(fname):
                os.remove(fname)

class MD5Info(dict):
    categories = 'good bad unknown'.split()
    categories = dict((x, x + '_md5') for x in categories)

    def __str__(self):
        result = []
        for name in sorted(self.categories.itervalues()):
            result.append('%s = [' % name)
            for item in sorted(getattr(self, name)):
                result.append("        '%s'," % item)
            result.append(']\n')
        result.append('')
        return '\n'.join(result)

    def __init__(self):
        self.__dict__ = self
        self.changed = False
        for name in self.categories.itervalues():
            setattr(self, name, [])

    def find(self, checksum):
        sets = {}
        prev = set()
        for name, fullname in self.categories.iteritems():
            value = set(getattr(self, fullname))
            assert not value & prev, (name, value, prev)
            prev |= value
            sets[name] = value
        for name, sumset in sets.iteritems():
            if checksum in sumset:
                return name
        self.changed = True
        self.unknown_md5.append(checksum)
        return 'unknown'

def checkmd5(pdfpath, md5path, resultlist):
    if not os.path.exists(pdfpath):
        resultlist.append('File %s not generated' % os.path.basename(pdfpath))
        return 'fail'

    info = MD5Info()
    if os.path.exists(md5path):
        f = open(md5path, 'rb')
        exec f in info
        f.close()

    f = open(pdfpath, 'rb')
    data = f.read()
    f.close()
    m = hashlib.md5()
    m.update(data)
    m = m.hexdigest()
    resulttype = info.find(m)
    resultlist.append("Validity of file %s checksum '%s' is %s." % (os.path.basename(pdfpath), m, resulttype))
    if info.changed:
        f = open(md5path, 'wb')
        f.write(str(info))
        f.close()
    return resulttype

def run_single_textfile(inpfname):
    iprefix = os.path.splitext(inpfname)[0]
    basename = os.path.basename(iprefix)
    oprefix = os.path.join(PathInfo.outdir, basename)
    mprefix = os.path.join(PathInfo.md5dir, basename)
    style = iprefix + '.style'
    outpdf = oprefix + '.pdf'
    outtext = oprefix + '.log'
    md5file = mprefix + '.json'

    for fname in (outtext, outpdf):
        if os.path.exists(fname):
            os.remove(fname)

    args = PathInfo.runcmd + ['-v', inpfname]
    if os.path.exists(style):
        args.extend(('-s', style))
    args.extend(('-o', outpdf))
    result = textexec(args, cwd=PathInfo.rootdir)
    checkinfo = checkmd5(outpdf, md5file, result)
    print result[-1]
    print
    result.append('')
    outf = open(outtext, 'wb')
    outf.write('\n'.join(result))
    outf.close()
    return checkinfo

def run_textfiles(textfiles=None):
    if not textfiles:
        textfiles = glob.glob(os.path.join(PathInfo.inpdir, '*.txt'))
        textfiles.sort()
    results = {}
    for fname in textfiles:
        key = run_single_textfile(fname)
        results[key] = results.get(key, 0) + 1
    print
    print 'Final checksum statistics:',
    print ', '.join(sorted('%s=%s' % x for x in results.iteritems()))
    print


def parse_commandline():
    parser = OptionParser()
    parser.add_option('-c', '--coverage', action="store_true",
        dest='coverage', default=False,
        help='Generate coverage information.')
    parser.add_option('-k', '--keep_coverage', action="store_true",
        dest='keep_coverage', default=False,
        help='Keep coverage information from previous runs.')
    return parser

def main(args=None):
    parser = parse_commandline()
    options, args = parser.parse_args(copy(args))
    if options.coverage:
        PathInfo.add_coverage(options.keep_coverage)
    run_textfiles(args)


if __name__ == '__main__':
    main()
