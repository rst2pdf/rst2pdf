# -*- coding: utf-8 -*-

import os
import shlex

import nose.plugins.skip
import six

from autotest import MD5Info, PathInfo, checkmd5, dirname, globjoin, run_single
from execmgr import default_logger as log
from execmgr import textexec


class RunTest:
    def __init__(self, f):
        basename = os.path.basename(f)
        self.description = basename
        mprefix = os.path.join(PathInfo.md5dir, basename)[:-4]
        md5file = mprefix + '.json'
        ignfile = os.path.join(PathInfo.inpdir, basename[:-4]) + '.ignore'
        nopdffile = os.path.join(PathInfo.inpdir, basename[:-4]) + '.nopdf'
        self.skip = False
        self.whySkip = ""
        self.openIssue = False
        if not os.path.exists(nopdffile):
            info = MD5Info()
            if os.path.exists(ignfile):
                self.skip = True
                with open(ignfile, "r") as f:
                    self.whySkip = f.read()
            if os.path.exists(md5file):
                f = open(md5file, 'rb')
                if six.PY3:
                    six.exec_(f.read(), info)
                else:
                    six.exec_(f.read(), info)

                f.close()
            if info.good_md5 in [[], ['sentinel']]:
                # This is an open issue or something that can't be checked automatically
                self.openIssue = True

    def __call__(self, f):
        if self.skip:
            raise nose.plugins.skip.SkipTest(self.whySkip.rstrip())
        elif self.openIssue:
            assert False, 'Test has no known good output (Open Issue)'
        else:
            key, errcode = run_single(f)
            if key in ['incomplete']:
                raise nose.plugins.skip.SkipTest
            assert key == 'good', '%s is not good: %s' % (f, key)


def run_installed_single(inpfname):
    """Run a single installed test.

    Like run_single, but runs the test using the installed version of rst2pdf.
    """

    iprefix = os.path.splitext(inpfname)[0]
    basename = os.path.basename(iprefix)
    if os.path.exists(iprefix + '.ignore'):
        return 'ignored', 0

    oprefix = os.path.join(PathInfo.outdir, basename)
    mprefix = os.path.join(PathInfo.md5dir, basename)
    outpdf = oprefix + '.pdf'
    outtext = oprefix + '.log'
    md5file = mprefix + '.json'

    inpfname = iprefix + '.txt'
    style = iprefix + '.style'
    cli = iprefix + '.cli'
    if os.path.isfile(cli):
        f = open(cli)
        extraargs = shlex.split(f.read())
        f.close()
    else:
        extraargs = []
    args = (
        ['rst2pdf'] + ['--date-invariant', '-v', os.path.basename(inpfname)] + extraargs
    )
    if os.path.exists(style):
        args.extend(('-s', os.path.basename(style)))
    args.extend(('-o', outpdf))
    errcode, result = textexec(args, cwd=dirname(inpfname), python_proc=None)

    checkinfo = checkmd5(outpdf, md5file, result, None, errcode, iprefix)
    log(result, '')
    outf = open(outtext, 'wb')
    outf.write('\n'.join(result))
    outf.close()
    return checkinfo, errcode


class RunInstalledTest:
    def __init__(self, f):
        basename = os.path.basename(f)
        self.description = basename
        mprefix = os.path.join(PathInfo.md5dir, basename)[:-4]
        md5file = mprefix + '.json'
        ignfile = os.path.join(PathInfo.inpdir, basename[:-4]) + '.ignore'
        info = MD5Info()
        self.skip = False
        self.whySkip = ""
        self.openIssue = False
        if os.path.exists(ignfile):
            self.skip = True
            with open(ignfile, "r") as f:
                self.whySkip = f.read()
        if os.path.exists(md5file):
            f = open(md5file, 'rb')
            if six.PY3:
                six.exec_(f.read(), info)
            else:
                six.exec_(f.read(), info)
            f.close()
        if info.good_md5 in [[], ['sentinel']]:
            # This is an open issue or something that can't be checked automatically
            self.openIssue = True

    def __call__(self, f):
        if self.skip:
            raise nose.plugins.skip.SkipTest(self.whySkip.rstrip())
        elif self.openIssue:
            assert False, 'Test has no known good output (Open Issue)'
        else:
            key, errcode = run_installed_single(f)
            if key in ['incomplete']:
                raise nose.plugins.skip.SkipTest
            assert key == 'good', '%s is not good: %s' % (f, key)


class RunSphinxTest:
    def __init__(self, f):
        basename = os.path.basename(f[:-1])
        self.description = basename
        mprefix = os.path.join(PathInfo.md5dir, basename)
        md5file = mprefix + '.json'
        ignfile = os.path.join(PathInfo.inpdir, basename) + '.ignore'
        info = MD5Info()
        self.skip = False
        self.whySkip = ""
        self.openIssue = False

        if os.path.exists(ignfile):
            self.skip = True
            with open(ignfile, "r") as f:
                self.whySkip = f.read()
        if os.path.exists(md5file):
            f = open(md5file, 'rb')
            if six.PY3:
                six.exec_(f.read(), info)
            else:
                six.exec_(f.read(), info)

            f.close()
        if info.good_md5 in [[], ['sentinel']]:
            # This is an open issue or something that can't be checked automatically
            self.openIssue = True

    def __call__(self, f):
        if self.skip:
            raise nose.plugins.skip.SkipTest(self.whySkip.rstrip())
        elif self.openIssue:
            assert False, 'Test has no known good output (Open Issue)'
        else:
            key, errcode = run_single(f)
            if key in ['incomplete']:
                raise nose.plugins.skip.SkipTest
            assert key == 'good', '%s is not good: %s' % (f, key)


def regulartest():
    """Run regular (doctest-based) tests.

    To run these tests (similar to autotest), run::

        nosetests -i regulartest
    """
    testfiles = globjoin(PathInfo.inpdir, '*.txt')
    for fname in testfiles:
        yield RunTest(fname), fname


def releasetest():
    """Run release tests.

    To run these tests (after you run setup.py install), run::

        nosetests -i releasetest
    """
    testfiles = globjoin(PathInfo.inpdir, '*.txt')
    for fname in testfiles:
        yield RunInstalledTest(fname), fname


def sphinxtest():
    """Run Sphinx-based tests.

    To run these tests, run::

        nosetests -i sphinxtest
    """
    testfiles = globjoin(PathInfo.inpdir, 'sphinx*/')
    for fname in testfiles:
        yield RunSphinxTest(fname), fname


def setup():
    PathInfo.add_coverage()
