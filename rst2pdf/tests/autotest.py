#!/usr/bin/env python
# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$


'''
Copyright (c) 2009, Patrick Maupin, Austin, Texas

Automated testing for rst2pdf

See LICENSE.txt for licensing terms
'''

import os
import sys
import glob
import shutil
import shlex
from copy import copy
from optparse import OptionParser
from execmgr import textexec, default_logger as log
from pythonpaths import setpythonpaths

# md5 module deprecated, but hashlib not available in 2.4
try:
    import hashlib
except ImportError:
    import md5 as hashlib

description = '''
autotest.py reads .txt files (and optional associated .style and other files)
from the input directory and generates throw-away results (.pdf and .log) in
the output subdirectory.  It also maintains (with the help of the developers)
a database of unknown, good, and bad MD5 checksums for the .pdf output files
in the md5 subdirectory.

By default, it will process all the files in the input directory, but one or
more individual files can be explicitly specified on the command line.

Use of the -c and -a options can cause usage of an external coverage package
to generate a .coverage file for code coverage.
'''

def dirname(path):
    # os.path.dirname('abc') returns '', which is completely
    # useless for most purposes...
    return os.path.dirname(path) or '.'

def globjoin(*parts):
    # A very common pattern in this module
    return sorted(glob.glob(os.path.join(*parts)))

class PathInfo(object):
    '''  This class is just a namespace to avoid cluttering up the
         module namespace.  It is never instantiated.
    '''
    rootdir = os.path.realpath(dirname(__file__))
    bindir = os.path.abspath(os.path.join(rootdir, '..', '..', 'bin'))
    runfile = os.path.join(bindir, 'rst2pdf')
    inpdir = os.path.join(rootdir, 'input')
    outdir = os.path.join(rootdir, 'output')
    md5dir = os.path.join(rootdir, 'md5')

    if not os.path.exists(runfile):
        raise SystemExit('Use bootstrap.py and buildout to create executable')

    runcmd = [runfile]

    @classmethod
    def add_coverage(cls, keep=False):
        cls.runcmd[0:0] = ['coverage', 'run', '-a']
        fname = os.path.join(cls.rootdir, '.coverage')
        os.environ['COVERAGE_FILE'] = fname
        if not keep:
            if os.path.exists(fname):
                os.remove(fname)

    @classmethod
    def load_subprocess(cls):
        import rst2pdf.createpdf
        return rst2pdf.createpdf.main

class MD5Info(dict):
    ''' The MD5Info class is used to round-trip good, bad, unknown
        information to/from a .json file.
        For formatting reasons, the json module isn't used for writing,
        and since we're not worried about security, we don't bother using
        it for reading, either.
    '''

    # Category to dump new data into
    new_category = 'unknown'
    # Categories which always should be in file
    mandatory_categories = 'good bad'.split()

    # Sentinel to make manual changes and diffs easy
    sentinel = 'sentinel'
    # An empty list is one which is truly empty or which has a sentinel
    empty = [[], ['sentinel']]
    # Suffix for file items
    suffix = '_md5'

    def __str__(self):
        ''' Return the string to output to the MD5 file '''
        result = []
        for name, value in sorted(self.iteritems()):
            if not name.endswith(self.suffix):
                continue
            result.append('%s = [' % name)
            result.append(',\n'.join(["        '%s'"%item for item in sorted(value)]))
            result.append(']\n')
        result.append('')
        return '\n'.join(result)

    def __init__(self):
        self.__dict__ = self
        self.changed = False
        for name in self.mandatory_categories:
            setattr(self, name + self.suffix, [self.sentinel])

    def find(self, checksum):
        ''' find() has some serious side-effects.  If the checksum
            is found, the category it was found in is returned.
            If the checksum is not found, then it is automagically
            added to the unknown category.  In all cases, the
            data is prepped to output to the file (if necessary),
            and self.changed is set if the data is modified during
            this process.  Functional programming this isn't...

            A quick word about the 'sentinel'.  This value starts
            with an 's', which happens to sort > highest hexadecimal
            digit of 'f', so it is always a the end of the list.

            The only reason for the sentinel is to make the database
            either to work with.  Both to modify (by moving an MD5
            line from one category to another) and to diff.  This
            is because every hexadecimal line (every line except
            the sentinel) is guaranteed to end with a comma.
        '''
        sets = []
        newinfo = {}
        prev = set()
        sentinel = set([self.sentinel])
        for key, value in self.iteritems():
            if not key.endswith(self.suffix):
                continue
            value = set(value) - sentinel
            # Make sure same checksum didn't make it into two
            # different categories (that would be a committer screwup...)
            assert not value & prev, (name, value, prev)
            prev |= value
            sets.append((key, value))
            newinfo[key] = sorted(value | sentinel)

        result = self.new_category + self.suffix
        for key, sumset in sets:
            if checksum in sumset:
                result = key
                break
        else:
            mylist = newinfo.setdefault(result, [])
            myset = set(mylist) | set([checksum, self.sentinel])
            mylist[:] = sorted(myset)

        for key, value in newinfo.iteritems():
            if value != self.get(key):
                self.update(newinfo)
                print "Updating MD5 file"
                self.changed = True
                break
        assert result.endswith(self.suffix), result
        return result[:-len(self.suffix)]

def checkmd5(pdfpath, md5path, resultlist):
    ''' checkmd5 validates the checksum of a generated PDF
        against the database, both reporting the results,
        and updating the database to add this MD5 into the
        unknown category if this checksum is not currently
        in the database.

        It updates the resultlist with information to be
        printed and added to the log file, and returns
        a result of 'good', 'bad', 'fail', or 'unknown'
    '''
    if not os.path.exists(pdfpath):
        log(resultlist, 'File %s not generated' % os.path.basename(pdfpath))
        return 'fail'
    if os.path.isdir(pdfpath):
        pdffiles = globjoin(pdfpath, '*.pdf')
    else:
        pdffiles = [pdfpath]

    # Read the database
    info = MD5Info()
    if os.path.exists(md5path):
        f = open(md5path, 'rb')
        exec f in info
        f.close()

    # Generate the current MD5
    md5s = []
    for pdfpath in pdffiles:
        f = open(pdfpath, 'rb')
        data = f.read()
        f.close()
        m = hashlib.md5()
        m.update(data)
        md5s.append(m.hexdigest())
    m = ' '.join(md5s)

    # Check MD5 against database and update if necessary
    resulttype = info.find(m)
    log(resultlist, "Validity of file %s checksum '%s' is %s." % (os.path.basename(pdfpath), m, resulttype))
    if info.changed:
        f = open(md5path, 'wb')
        f.write(str(info))
        f.close()
    return resulttype


def build_sphinx(sphinxdir, outpdf):
    def getbuilddirs():
        return globjoin(sphinxdir, '*build*')

    for builddir in getbuilddirs():
        shutil.rmtree(builddir)
    errcode, result = textexec('make pdf', cwd=sphinxdir)
    builddirs = getbuilddirs()
    if len(builddirs) != 1:
        log(result, 'Cannot determine build directory')
        return 1, result
    builddir, = builddirs
    pdfdir = os.path.join(builddir, 'pdf')
    pdffiles = globjoin(pdfdir, '*.pdf')
    if len(pdffiles) == 1:
        shutil.copyfile(pdffiles[0], outpdf)
    elif not pdffiles:
        log(result, 'Output PDF apparently not generated')
        errcode = 1
    else:
        shutil.copytree(pdfdir, outpdf)
    return errcode, result

def build_txt(iprefix, outpdf, fastfork):
        inpfname = iprefix + '.txt'
        style = iprefix + '.style'
        cli = iprefix + '.cli'
        if os.path.isfile(cli):
            f = open(cli)
            extraargs=shlex.split(f.read())
            f.close()
        else:
            extraargs=[]
        args = PathInfo.runcmd + ['--date-invariant', '-v', os.path.basename(inpfname)]+extraargs
        if os.path.exists(style):
            args.extend(('-s', os.path.basename(style)))
        args.extend(('-o', outpdf))
        return textexec(args, cwd=dirname(inpfname), python_proc=fastfork)

def run_single_test(inpfname, incremental=False, fastfork=None):
    use_sphinx = 'sphinx' in inpfname
    if use_sphinx:
        sphinxdir = inpfname
        if sphinxdir.endswith('Makefile'):
            sphinxdir = dirname(sphinxdir)
        basename = os.path.basename(sphinxdir)
    else:
        iprefix = os.path.splitext(inpfname)[0]
        basename = os.path.basename(iprefix)
        if os.path.exists(iprefix + '.ignore'):
            return 'ignored', 0

    oprefix = os.path.join(PathInfo.outdir, basename)
    mprefix = os.path.join(PathInfo.md5dir, basename)
    outpdf = oprefix + '.pdf'
    outtext = oprefix + '.log'
    md5file = mprefix + '.json'

    if incremental and os.path.exists(outpdf):
        return 'preexisting', 0

    for fname in (outtext, outpdf):
        if os.path.exists(fname):
            if os.path.isdir(fname):
                shutil.rmtree(fname)
            else:
                os.remove(fname)

    if use_sphinx:
        errcode, result = build_sphinx(sphinxdir, outpdf)
    else:
        errcode, result = build_txt(iprefix, outpdf, fastfork)

    checkinfo = checkmd5(outpdf, md5file, result)
    log(result, '')
    outf = open(outtext, 'wb')
    outf.write('\n'.join(result))
    outf.close()
    return checkinfo, errcode

def run_testlist(testfiles=None, incremental=False, fastfork=None, do_text= False, do_sphinx=False):
    if not testfiles:
        testfiles = []
        if do_text:
            testfiles = globjoin(PathInfo.inpdir, '*.txt')
            testfiles += globjoin(PathInfo.inpdir, '*', '*.txt')
            testfiles = [x for x in testfiles if 'sphinx' not in x]
        if do_sphinx:
            testfiles += globjoin(PathInfo.inpdir, 'sphinx*')
    results = {}
    for fname in testfiles:
        key, errcode = run_single_test(fname, incremental, fastfork)
        results[key] = results.get(key, 0) + 1
        if incremental and errcode and 0:
            break
    print
    print 'Final checksum statistics:',
    print ', '.join(sorted('%s=%s' % x for x in results.iteritems()))
    print

def parse_commandline():
    usage = '%prog [options] [<input.txt file> [<input.txt file>]...]'
    parser = OptionParser(usage, description=description)
    parser.add_option('-c', '--coverage', action="store_true",
        dest='coverage', default=False,
        help='Generate new coverage information.')
    parser.add_option('-a', '--add-coverage', action="store_true",
        dest='add_coverage', default=False,
        help='Add coverage information to previous runs.')
    parser.add_option('-i', '--incremental', action="store_true",
        dest='incremental', default=False,
        help='Incremental build -- ignores existing PDFs')
    parser.add_option('-f', '--fast', action="store_true",
        dest='fastfork', default=False,
        help='Fork and reuse process information')
    parser.add_option('-s', '--sphinx', action="store_true",
        dest='sphinx', default=False,
        help='Run sphinx tests only')
    parser.add_option('-e', '--everything', action="store_true",
        dest='everything', default=False,
        help='Run both rst2pdf and sphinx tests')
    parser.add_option('-p', '--python-path', action="store_true",
        dest='nopythonpath', default=False,
        help='Do not set up PYTHONPATH env variable')
    return parser

def main(args=None):
    parser = parse_commandline()
    options, args = parser.parse_args(copy(args))
    if not options.nopythonpath:
        setpythonpaths(PathInfo.runfile, PathInfo.rootdir)
    fastfork = None
    do_sphinx = options.sphinx or options.everything
    do_text = options.everything or not options.sphinx
    if options.coverage or options.add_coverage:
        assert not options.fastfork, "Cannot fastfork and run coverage simultaneously"
        assert not do_sphinx, "Cannot run sphinx and coverage simultaneously"
        PathInfo.add_coverage(options.add_coverage)
    elif options.fastfork:
        fastfork = PathInfo.load_subprocess()
    run_testlist(args, options.incremental, fastfork, do_text, do_sphinx)

if __name__ == '__main__':
    main()
