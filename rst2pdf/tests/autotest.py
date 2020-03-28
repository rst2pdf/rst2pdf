#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2009, Patrick Maupin, Austin, Texas

Automated testing for rst2pdf

See LICENSE.txt for licensing terms
'''

import distutils.spawn
import glob
import os
import shlex
import shutil
import subprocess
import tempfile
from copy import copy
from optparse import OptionParser

from execmgr import default_logger as log
from execmgr import textexec
from pythonpaths import setpythonpaths
from six import print_

description = '''
autotest.py reads .txt files (and optional associated .style and other files)
from the input directory and generates throw-away results (.pdf and .log) in
the output subdirectory. These are visually compared to the reference PDFs
found in ``reference`` and any differences are flagged as errors.

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
    inpdir = os.path.join(rootdir, 'input')
    refdir = os.path.join(rootdir, 'reference')
    outdir = os.path.join(rootdir, 'output')

    runfile = distutils.spawn.find_executable('rst2pdf')
    assert runfile, 'rst2pdf executable not found, install it with setup.py'

    if not os.path.exists(outdir):
        os.mkdir(outdir)

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


def _get_error_code(result_type):
    error_codes = ['good', 'bad', 'fail', 'unknown']
    try:
        error_code = error_codes.index(result_type)
    except ValueError:
        error_code = 4

    return error_code


def validate_pdf(test_name, ref_dir=None, out_dir=None):
    # https://stackoverflow.com/q/5132749/

    ref_dir = ref_dir or PathInfo.refdir
    out_dir = out_dir or PathInfo.outdir

    ref_pdf = os.path.join(ref_dir, test_name + '.pdf')
    out_pdf = os.path.join(out_dir, test_name + '.pdf')

    if os.path.isdir(ref_pdf):
        ref_pdfs = [os.path.splitext(x)[0] for x in os.listdir(ref_pdf)]
        for ref in ref_pdfs:
            validate_pdf(ref, ref_dir=ref_pdf, out_dir=out_pdf)

        return

    # make sure we actually have something to work with first

    if not all(os.path.exists(x) for x in (ref_pdf, out_pdf)):
        log([], 'Not all files exist; is a reference missing?')
        return ('fail', _get_error_code('fail'))

    # figure out how many pages are in each PDF - it should be identical

    cmd = ['pdfinfo']

    ref_pages = 0
    out_pages = 0

    for pdf in (ref_pdf, out_pdf):
        try:
            out = subprocess.check_output(
                cmd + [pdf], stderr=subprocess.STDOUT
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            log(
                [],
                'Failed to count number of pages in PDF - is pdfinfo installed?',
            )
            log([], str(exc))
            return ('fail', _get_error_code('fail'))

        pages = 0
        for line in out.split('\n'):
            if line.startswith('Pages:'):
                pages = int(line.split()[1])
                break

        if pdf == ref_pdf:
            ref_pages = pages
        else:
            out_pages = pages

    if ref_pages != out_pages:
        log(
            [],
            'PDFs appear to have different page counts (reference=%d, '
            'output=%d)' % (ref_pages, out_pages),
        )
        return ('bad', _get_error_code('bad'))

    diffs = []

    for page in range(ref_pages):
        diff_png = os.path.join(out_dir, test_name + '-%d.diff.png' % page)

        # we have minimal amount of fuzzing and grayscale colorspace since that limits
        # the possibility of false positives due to changes in imagemagick or similar
        cmd = [
            'compare',
            '-colorspace',
            'GRAY',
            '-metric',
            'AE',
            '-fuzz',
            '5%',
            '%s[%d]' % (ref_pdf, page),
            '%s[%d]' % (out_pdf, page),
            diff_png,
        ]

        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except (OSError, subprocess.CalledProcessError) as exc:
            # if this returned with a non-zero 0 code, we either have a
            # different PDF or there was an issue with the command
            if isinstance(exc, OSError) or not exc.output.isdigit():
                log(
                    [],
                    'Failed to convert PDFs to PNG - is ImageMagick installed?',
                )
                log([], str(exc))
                return ('fail', _get_error_code('fail'))

            out = exc.output

        diffs.append((int(out.strip()), diff_png))

    # if there's no difference on any page, we're good and can return success
    if not any(ae for ae, _ in diffs):
        log([], 'PDFs appear to be identical')
        return ('good', _get_error_code('good'))

    # otherwise we log the absolute error (AE) for each page that's incorrect
    log(
        [],
        'PDFs appear to be different (%s)'
        % ', '.join(
            [
                'page %d = %f' % (page + 1, result[0])
                for page, result in enumerate(diffs)
                if result[0]
            ]
        ),
    )
    log([], 'Diffs saved to %s' % out_dir)
    return ('bad', _get_error_code('bad'))


def build_sphinx(sphinxdir, outpdf):
    builddir = tempfile.mkdtemp(prefix='rst2pdf-sphinx-')
    errcode, result = textexec(
        "sphinx-build -b pdf %s %s" % (os.path.abspath(sphinxdir), builddir)
    )
    pdffiles = globjoin(builddir, '*.pdf')
    if len(pdffiles) == 1:
        shutil.copyfile(pdffiles[0], outpdf)
    elif not pdffiles:
        log(result, 'Output PDF apparently not generated')
        errcode = 1
    else:
        shutil.copytree(builddir, outpdf)
    return errcode, result


def build_txt(iprefix, outpdf, fastfork):
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
        PathInfo.runcmd
        + ['--date-invariant', '-v', os.path.basename(inpfname)]
        + extraargs
    )
    if os.path.exists(style):
        args.extend(('-s', os.path.basename(style)))
    args.extend(('-o', outpdf))
    return textexec(args, cwd=dirname(inpfname), python_proc=fastfork)


def run_single(
    inpfname, incremental=False, fastfork=None, ignore_ignorefile=False
):
    use_sphinx = 'sphinx' in inpfname and os.path.isdir(inpfname)
    if use_sphinx:
        sphinxdir = inpfname
        if sphinxdir.endswith('Makefile'):
            sphinxdir = dirname(sphinxdir)
        basename = os.path.basename(sphinxdir)
        if not basename:
            sphinxdir = os.path.dirname(sphinxdir)
            basename = os.path.basename(sphinxdir)
        if os.path.exists(sphinxdir + '.ignore'):
            if ignore_ignorefile:
                log([], 'Ignoring ' + sphinxdir + '.ignore file')
            else:
                f = open(sphinxdir + '.ignore', 'r')
                data = f.read()
                f.close()
                log([], 'Ignored: ' + data)
                return 'ignored', 0
    else:
        iprefix = os.path.splitext(inpfname)[0]
        basename = os.path.basename(iprefix)
        if os.path.exists(iprefix + '.ignore'):
            if ignore_ignorefile:
                log([], 'Ignoring ' + iprefix + '.ignore file')
            else:
                f = open(iprefix + '.ignore', 'r')
                data = f.read()
                f.close()
                log([], 'Ignored: ' + data)
                return 'ignored', 0

    oprefix = os.path.join(PathInfo.outdir, basename)
    outpdf = oprefix + '.pdf'
    outtext = oprefix + '.log'

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
        checkinfo, errcode = validate_pdf(basename)
    else:
        errcode, result = build_txt(iprefix, outpdf, fastfork)
        checkinfo, errcode = validate_pdf(basename)

    log(result, '')
    outf = open(outtext, 'w')
    outf.write('\n'.join(result))
    outf.close()

    return checkinfo, errcode


def run_testlist(
    testfiles=None,
    incremental=False,
    fastfork=None,
    do_text=False,
    do_sphinx=False,
    ignore_ignorefile=False,
):
    returnErrorCode = 0
    if not testfiles:
        testfiles = []
        if do_text:
            testfiles = globjoin(PathInfo.inpdir, '*.txt')
            testfiles += globjoin(PathInfo.inpdir, '*', '*.txt')
            testfiles = [(x, fastfork) for x in testfiles if 'sphinx' not in x]
        if do_sphinx:
            testfiles += [
                (x, None) for x in globjoin(PathInfo.inpdir, 'sphinx*')
            ]
    else:
        testfiles = [(x, fastfork) for x in testfiles]

    results = {}
    for fname, fastfork in testfiles:
        key, errcode = run_single(
            fname, incremental, fastfork, ignore_ignorefile
        )
        if errcode != 0:
            returnErrorCode = errcode
        results[key] = results.get(key, 0) + 1
        if incremental and errcode and 0:
            break
    print_('\nFinal checksum statistics:')
    print_(', '.join(sorted('%s=%s' % x for x in results.items())))
    print_('\n')

    return returnErrorCode


def parse_commandline():
    usage = '%prog [options] [<input.txt file> [<input.txt file>]...]'
    parser = OptionParser(usage, description=description)
    parser.add_option(
        '-c',
        '--coverage',
        action="store_true",
        dest='coverage',
        default=False,
        help='Generate new coverage information.',
    )
    parser.add_option(
        '-a',
        '--add-coverage',
        action="store_true",
        dest='add_coverage',
        default=False,
        help='Add coverage information to previous runs.',
    )
    parser.add_option(
        '-i',
        '--incremental',
        action="store_true",
        dest='incremental',
        default=False,
        help='Incremental build -- ignores existing PDFs',
    )
    parser.add_option(
        '-I',
        '--ignore-ignore',
        action="store_true",
        dest='ignore_ignorefile',
        default=False,
        help='Ignore .ignore file',
    )
    parser.add_option(
        '-f',
        '--fast',
        action="store_true",
        dest='fastfork',
        default=False,
        help='Fork and reuse process information',
    )
    parser.add_option(
        '-s',
        '--sphinx',
        action="store_true",
        dest='sphinx',
        default=False,
        help='Run sphinx tests only',
    )
    parser.add_option(
        '-e',
        '--everything',
        action="store_true",
        dest='everything',
        default=False,
        help='Run both rst2pdf and sphinx tests',
    )
    parser.add_option(
        '-p',
        '--python-path',
        action="store_true",
        dest='nopythonpath',
        default=False,
        help='Do not set up PYTHONPATH env variable',
    )
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
        assert (
            not options.fastfork
        ), "Cannot fastfork and run coverage simultaneously"
        assert not do_sphinx, "Cannot run sphinx and coverage simultaneously"
        PathInfo.add_coverage(options.add_coverage)
    elif options.fastfork:
        fastfork = PathInfo.load_subprocess()
    errcode = run_testlist(
        args,
        options.incremental,
        fastfork,
        do_text,
        do_sphinx,
        options.ignore_ignorefile,
    )
    exit(errcode)


if __name__ == '__main__':
    main()
