# -*- coding: utf-8 -*-

import os
import shlex
import shutil
import subprocess
import tempfile

from itertools import zip_longest
from pathlib import Path

import nose.plugins.skip
import PyPDF2

# TODO:  rst2pdf currently does some crazy magic with extensions and globals
# that mean everything must be completely reloaded for each test to keep them
# isolated.  The easiest way at the moment is to simply call the executable
# rather than try to load `rst2pdf.main`, but this will need to change once
# the handling of globals is fixed.

def pdf_pages(pdf):
    """
    Open a PDF file and yield each page as a temporary PDF file.
    """
    with pdf.open('rb') as fh:
        reader = PyPDF2.PdfFileReader(fh)
        for pagenum in range(reader.getNumPages()):
            page = reader.getPage(pagenum)
            writer = PyPDF2.PdfFileWriter()
            writer.addPage(page)
            with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
                writer.write(tmp)
                tmp.flush()
                yield tmp


def compare_files(got, expect):
    """
    Compare two pdfs page by page and determine percentage difference.

    Pages are compared pixel by pixel using ImageMagick's ``convert``.  If the
    total percentage difference is greater than ``threshold``, the test fails.
    If the number of pages differs, the test also fails.
    """
    got_pages = pdf_pages(got)
    expect_pages = pdf_pages(expect)
    iterpages = zip_longest(got_pages, expect_pages)
    error_pages = []
    for pagenum, (got_page, expect_page) in enumerate(iterpages):
        assert None not in (got_page, expect_page), 'EOF at page %d' % pagenum
        diff_page = got.parent / ('diff_%d.png' % (pagenum + 1))
        args = [
            'compare',
            got_page.name,
            expect_page.name,
            '-metric',
            'AE',
            str(diff_page)
        ]
        match_code = subprocess.call(args, stderr=subprocess.DEVNULL)
        if match_code != 0:
            error_pages.append(pagenum + 1)
    assert len(error_pages) == 0, \
        'Page match error on pages {}'.format(str(error_pages))


def build_sphinx(path):
    sphinx_path = path / 'sphinx'
    os.chdir(str(sphinx_path))
    env = os.environ.copy()
    env['SPHINXOPTS'] = '-Q'
    proc = subprocess.Popen(
        ['make', 'clean', 'pdf'],
        cwd=str(sphinx_path),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        out, err = proc.communicate(5)
    except subprocess.TimeoutExpired:
        print('-----> STDOUT')
        print(out)
        print('-----> STDERR')
        print(err)
        raise
    pdfs = list(sphinx_path.glob('_build/pdf/*.pdf'))
    if len(pdfs) > 1:
        (path / 'output.pdf').mkdir()
    for pdf in pdfs:
        shutil.copy(str(pdf), str(path / 'output.pdf'))
    return proc.returncode


def build_txt(path):
    os.chdir(str(path))
    inpfname = path / 'input.txt'
    style = path / 'input.style'
    cli = path / 'input.cli'
    outname = path / 'output.pdf'
    args = ['rst2pdf', '--date-invariant', '-v', str(inpfname), '-o', str(outname)]
    if cli.is_file():
        with cli.open('r') as f:
            args += shlex.split(f.read())
    if style.is_file():
        args += ['-s', str(style)]
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        out, err = proc.communicate(5)
    except subprocess.TimeoutExpired:
        print('-----> STDOUT')
        print(out)
        print('-----> STDERR')
        print(err)
        raise
    return proc.returncode


class RunTest:

    def __init__(self, path):
        self.path = path
        self.description = path.name

    def __call__(self):
        if (self.path / 'ignore').exists():
            raise nose.plugins.skip.SkipTest
        use_sphinx = self.path.stem.startswith('sphinx')
        if use_sphinx:
            errcode = build_sphinx(self.path)
        else:
            errcode = build_txt(self.path)
        assert errcode == 0
        self.compare()

    def compare(self):
        got = self.path / 'output.pdf'
        expect = self.path / 'expected_output.pdf'
        if got.is_dir():
            for gotpdf in got.iterdir():
                expectpdf = expect / gotpdf.name
                assert expectpdf.exists()
                compare_files(gotpdf, expectpdf)
        else:
            compare_files(got, expect)


def test_files():
    """
    Runs all PDF tests
    """
    root = Path(__file__).parent / 'testcases'
    # Clean old files.  Don't do this as part of teardown, because they will
    # probably be useful for post-mortems.
    for f in root.glob('*/output.pdf'):
        if f.is_dir():
            shutil.rmtree(str(f))
        else:
            f.unlink()
    for f in root.glob('*/diff*.png'):
        f.unlink()
    for d in root.glob('*/sphinx/_build'):
        shutil.rmtree(str(d))

    tests = sorted((d for d in root.iterdir() if d.is_dir()),
                   key=lambda p: p.name)
    for path in tests:
        yield RunTest(path)
