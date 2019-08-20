# -*- coding: utf-8 -*-

import os
import shlex

import nose.plugins.skip

from autotest import PathInfo, dirname, globjoin, run_single, validate_pdf
from execmgr import default_logger as log
from execmgr import textexec


class RunTest:
    def __init__(self, f):
        basename = os.path.basename(f)

        self.description = basename
        self.skip = False
        self.whySkip = ''

        no_pdf_file = os.path.join(PathInfo.inpdir, basename[:-4]) + '.nopdf'
        if os.path.exists(no_pdf_file):
            return

        ignore_file = os.path.join(PathInfo.inpdir, basename[:-4]) + '.ignore'
        if os.path.exists(ignore_file):
            self.skip = True
            with open(ignore_file, "r") as f:
                self.whySkip = f.read()

    def __call__(self, f):
        if self.skip:
            raise nose.plugins.skip.SkipTest(self.whySkip.rstrip())

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
    outpdf = oprefix + '.pdf'
    outtext = oprefix + '.log'

    inpfname = iprefix + '.txt'
    style = iprefix + '.style'
    cli = iprefix + '.cli'

    cmd = ['rst2pdf', '--date-invariant', '-v', os.path.basename(inpfname)]

    if os.path.isfile(cli):
        with open(cli) as fh:
            cmd.extend(shlex.split(fh.read()))

    if os.path.exists(style):
        cmd.extend(('-s', os.path.basename(style)))

    cmd.extend(('-o', outpdf))

    errcode, result = textexec(cmd, cwd=dirname(inpfname), python_proc=None)
    checkinfo, errcode = validate_pdf(basename)

    log(result, '')
    with open(outtext, 'wb') as fh:
        fh.write('\n'.join(result))

    return checkinfo, errcode


class RunInstalledTest:
    def __init__(self, f):
        basename = os.path.basename(f)

        self.description = basename
        self.skip = False
        self.whySkip = ''

        ignore_file = os.path.join(PathInfo.inpdir, basename[:-4]) + '.ignore'
        if os.path.exists(ignore_file):
            self.skip = True
            with open(ignore_file, 'r') as f:
                self.whySkip = f.read()

    def __call__(self, f):
        if self.skip:
            raise nose.plugins.skip.SkipTest(self.whySkip.rstrip())

        key, errcode = run_installed_single(f)
        if key in ['incomplete']:
            raise nose.plugins.skip.SkipTest

        assert key == 'good', '%s is not good: %s' % (f, key)


class RunSphinxTest:
    def __init__(self, f):
        basename = os.path.basename(f[:-1])

        self.description = basename
        self.skip = False
        self.whySkip = ''

        ignore_file = os.path.join(PathInfo.inpdir, basename) + '.ignore'
        if os.path.exists(ignore_file):
            self.skip = True
            with open(ignore_file, 'r') as f:
                self.whySkip = f.read()

    def __call__(self, f):
        if self.skip:
            raise nose.plugins.skip.SkipTest(self.whySkip.rstrip())

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
