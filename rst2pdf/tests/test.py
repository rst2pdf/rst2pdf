# -*- coding: utf-8 -*-

import glob
import os
import shlex
import shutil
import subprocess
import tempfile

from itertools import zip_longest, count

import nose.plugins.skip
import PyPDF2

from execmgr import textexec

from rst2pdf import createpdf as rst2pdf


def dirname(path):
    # os.path.dirname('abc') returns '', which is completely
    # useless for most purposes...
    return os.path.dirname(path) or '.'


def globjoin(*parts):
    # A very common pattern in this module
    return sorted(glob.glob(os.path.join(*parts)))


class PathInfo:

    """
    This class is just a namespace to avoid cluttering up the
    module namespace.  It is never instantiated.
    """

    rootdir = os.path.realpath(dirname(__file__))
    bindir = os.path.abspath(os.path.join(rootdir, '..', '..', 'bin'))
    inpdir = os.path.join(rootdir, 'input')
    outdir = os.path.join(rootdir, 'output')
    expectdir = os.path.join(rootdir, 'expected_output')
    md5dir = os.path.join(rootdir, 'md5')
    runcmd = ['rst2pdf']


def pdf_pages(pdf):
    """
    Open a PDF file and yield each page as a temporary PDF file.
    """
    with open(pdf, 'rb') as fh:
        reader = PyPDF2.PdfFileReader(fh)
        for pagenum in range(reader.getNumPages()):
            page = reader.getPage(pagenum)
            writer = PyPDF2.PdfFileWriter()
            writer.addPage(page)
            with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
                writer.write(tmp)
                tmp.flush()
                yield tmp


def compare_pdfs(got, expect, threshold=0):
    """
    Compare two pdfs page by page and determine percentage difference.

    Pages are compared pixel by pixel using ImageMagick's ``convert``.  If the
    total percentage difference is greater than ``threshold``, the test fails.
    If the number of pages differs, the test also fails.
    """
    got_pages = pdf_pages(got)
    expect_pages = pdf_pages(expect)
    iterpages = zip_longest(count(), got_pages, expect_pages)
    for pagenum, got_page, expect_page in iterpages:
        assert None not in (got_page, expect_page), 'EOF at page %d' % pagenum
        args = [
            'convert',
            got_page.name,
            expect_page.name,
            '-compose',
            'difference',
            '-composite',
            '-format',
            "'%[mean]'",
            "info:"
        ]
        diff_percent = subprocess.check_output(args).decode()
        diff_percent = float(diff_percent.strip("'"))
        assert diff_percent <= threshold, \
            'Page {} differs by {:.3f}% (> {:.3f})'.format(
                pagenum + 1, diff_percent, threshold)


def build_sphinx(sphinxdir, outpdf):
    def getbuilddirs():
        return globjoin(sphinxdir, '*build*')

    for builddir in getbuilddirs():
        shutil.rmtree(builddir)
    errcode = textexec('make clean pdf', cwd=sphinxdir)
    builddirs = getbuilddirs()
    if len(builddirs) != 1:
        return 1
    builddir, = builddirs
    pdfdir = os.path.join(builddir, 'pdf')
    pdffiles = globjoin(pdfdir, '*.pdf')
    if len(pdffiles) == 1:
        shutil.copyfile(pdffiles[0], outpdf)
    elif not pdffiles:
        errcode = 1
    else:
        shutil.copytree(pdfdir, outpdf)
    return errcode


def build_txt(iprefix, outpdf):
    inpfname = iprefix + '.txt'
    style = iprefix + '.style'
    cli = iprefix + '.cli'
    if os.path.isfile(cli):
        with open(cli, 'r') as f:
            extraargs = shlex.split(f.read())
    else:
        extraargs = []
    args = ['--date-invariant', '-v', inpfname] + extraargs
    if os.path.exists(style):
        args += ['-s', style]
    args.extend(['-o', outpdf])
    return rst2pdf.main(args)


def run_single(inpfname):
    use_sphinx = 'sphinx' in inpfname and os.path.isdir(inpfname)
    if use_sphinx:
        sphinxdir = inpfname
        if sphinxdir.endswith('Makefile'):
            sphinxdir = dirname(sphinxdir)
        basename = os.path.basename(sphinxdir)
        if not basename:
            sphinxdir = os.path.dirname(sphinxdir)
            basename = os.path.basename(sphinxdir)
    else:
        iprefix = os.path.splitext(inpfname)[0]
        basename = os.path.basename(iprefix)
        if os.path.exists(iprefix + '.ignore'):
            raise nose.plugins.skip.SkipTest

    oprefix = os.path.join(PathInfo.outdir, basename)
    expect_pdf = os.path.join(PathInfo.expectdir, basename) + '.pdf'
    outpdf = oprefix + '.pdf'
    outtext = oprefix + '.log'

    for fname in (outtext, outpdf):
        if os.path.exists(fname):
            if os.path.isdir(fname):
                shutil.rmtree(fname)
            else:
                os.remove(fname)

    if use_sphinx:
        errcode = build_sphinx(sphinxdir, outpdf)
    else:
        errcode = build_txt(iprefix, outpdf)
    assert errcode == 0
    compare_pdfs(outpdf, expect_pdf)


class RunTest:

    def __init__(self, f):
        basename = os.path.basename(f)
        self.description = basename
        mprefix = os.path.join(PathInfo.md5dir, basename)[:-4]
        md5file = mprefix + '.json'
        ignfile = os.path.join(PathInfo.inpdir, basename[:-4]) + '.ignore'
        self.skip = False
        self.openIssue = False
        if os.path.exists(ignfile):
            self.skip = True
        info = {}
        if os.path.exists(md5file):
            with open(md5file, 'r') as f:
                exec(f.read(), info)
        if info.get('good_md5') in [[], ['sentinel']]:
            # This is an open issue or something that can't be checked automatically
            self.openIssue = True

    def __call__(self, f):
        if self.skip:
            raise nose.plugins.skip.SkipTest
        elif self.openIssue:
            assert False, 'Test has no known good output (Open Issue)'
        else:
            run_single(f)


class RunSphinxTest(RunTest):

    def __init__(self, f):
        basename = os.path.basename(f[:-1])
        self.description = basename
        mprefix = os.path.join(PathInfo.md5dir, basename)
        md5file = mprefix + '.json'
        ignfile = os.path.join(PathInfo.inpdir, basename) + '.ignore'
        self.skip = False
        self.openIssue = False

        if os.path.exists(ignfile):
            self.skip = True
        info = {}
        if os.path.exists(md5file):
            with open(md5file, 'r') as f:
                exec(f.read(), info)
        if info.get('good_md5') in [[], ['sentinel']]:
            # This is an open issue or something that can't be checked automatically
            self.openIssue = True


def test_regular():
    """
    Test all regular text files
    """
    os.chdir(PathInfo.inpdir)
    testfiles = globjoin(PathInfo.inpdir, '*.txt')
    for fname in testfiles:
        yield RunTest(fname), fname


def test_sphinx():
    """
    Test files which need to be compiled by sphinx
    """
    testfiles = globjoin(PathInfo.inpdir, 'sphinx*/')
    for fname in testfiles:
        os.chdir(fname)
        yield RunSphinxTest(fname), fname
