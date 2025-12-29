"""
Copyright (c) 2020, Stephen Finucane <stephen@that.guru>

Automated testing for rst2pdf.

See LICENSE.txt for licensing terms
"""

import glob
import os
import shlex
import shutil
import subprocess
import tempfile

from packaging import version
import pytest

try:
    import fitz
except ImportError:
    import fitz_old as fitz


ROOT_DIR = os.path.realpath(os.path.dirname(__file__))
INPUT_DIR = os.path.join(ROOT_DIR, 'input')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
REFERENCE_DIR = os.path.join(ROOT_DIR, 'reference')


def can_run(command_list):
    def _can_run():
        try:
            p = subprocess.Popen(
                command_list,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            p.terminate()
        except FileNotFoundError:
            return False
        return True

    return _can_run


check_dependency = {'plantuml': can_run(["plantuml", "-pipe"])}


def _get_metadata(pdf):
    metadata = pdf.metadata

    # Do not compare dates as they will differ each time the PDF is generated
    del metadata['creationDate']
    del metadata['modDate']

    # Do not compare the ReportLab producer string as it may differ between versions
    del metadata['producer']

    return metadata


def _get_pages(pdf):
    pages = []

    for page in pdf.pages():
        pages.append(page.get_text('blocks'))

    return pages


def compare_pdfs(path_a, path_b):
    try:
        pdf_a = fitz.open(path_a)
    except RuntimeError:
        pytest.fail(
            'Reference file at %r is not a valid PDF.'
            % (os.path.relpath(path_a, ROOT_DIR),),
            pytrace=False,
        )

    try:
        pdf_b = fitz.open(path_b)
    except RuntimeError:
        pytest.fail(
            'Output file at %r is not a valid PDF.'
            % (os.path.relpath(path_b, ROOT_DIR),),
            pytrace=False,
        )

    # sanity check

    assert pdf_a.is_pdf
    assert pdf_b.is_pdf

    # compare metadata

    assert _get_metadata(pdf_a) == _get_metadata(pdf_b)

    # compare content

    pages_a = _get_pages(pdf_a)
    pages_b = _get_pages(pdf_b)

    def fuzzy_coord_diff(coord_a, coord_b):
        diff = abs(coord_a - coord_b)
        threshold = 3  # 3 px is approximately 1.06mm
        assert (
            diff < threshold
        ), "Coordinates of the last printed block differs from the reference"

    def fuzzy_string_diff(string_a, string_b):
        a_is_image = string_a.startswith("<image: DeviceRGB")
        b_is_image = string_b.startswith("<image: DeviceRGB")
        if a_is_image and b_is_image:
            # We can't necessarily control the image metadata text in the block (e.g. from plantuml), so we do not
            # check it.
            return

        words_a = string_a.split()
        words_b = string_b.split()
        assert (
            words_a == words_b
        ), "Text of the last printed block differs from the reference"

    assert len(pages_a) == len(pages_b), "Number of pages differs from the reference"
    page_no = 0
    for page_a, page_b in zip(pages_a, pages_b):
        page_no = page_no + 1
        print(f"++ Page {page_no} ++")
        print(f"page_a: {page_a}")
        print(f"page_b: {page_b}")
        print("number of blocks in page_a: %s" % len(page_a))
        print("number of blocks in page_b: %s" % len(page_b))
        assert len(page_a) == len(
            page_b
        ), f"Number of blocks on page {page_no} differs from the reference"
        for block_a, block_b in zip(page_a, page_b):
            # each block has the following format:
            #
            # (x0, y0, x1, y1, "lines in block", block_type, block_no)
            #
            # block_type and block_no should remain unchanged, but it's
            # possible for the blocks to move around the document slightly and
            # the text refold without breaking entirely
            print(f"block_a: {block_a}")
            print(f"block_b: {block_b}")
            fuzzy_coord_diff(block_a[0], block_b[0])
            fuzzy_coord_diff(block_a[1], block_b[1])
            fuzzy_coord_diff(block_a[2], block_b[2])
            fuzzy_coord_diff(block_a[3], block_b[3])
            fuzzy_string_diff(block_a[4], block_b[4])
            assert block_a[5] == block_b[5]
            assert block_a[6] == block_b[6]


class File(pytest.File):

    if version.parse(pytest.__version__) < version.parse('5.4.0'):

        @classmethod
        def from_parent(cls, parent, path):
            return cls(parent=parent, path=path)


class RstFile(File):
    def collect(self):
        name = os.path.splitext(self.fspath.basename)[0]
        yield RstItem.from_parent(parent=self, name=name)


class SphinxFile(File):
    def collect(self):
        name = os.path.split(self.fspath.dirname)[-1]
        yield SphinxItem.from_parent(parent=self, name=name)


class Item(pytest.Item):

    if version.parse(pytest.__version__) < version.parse('5.4.0'):

        @classmethod
        def from_parent(cls, parent, name):
            return cls(parent=parent, name=name)

    def _build(self):
        raise NotImplementedError

    def _fail(self, msg, output=None):
        pytest.fail(
            f'{msg}: \n\n{output.decode("utf-8")}' if output else msg,
            pytrace=False,
        )

    def runtest(self):
        __tracebackhide__ = True

        # if '.ignore' file present, skip test

        ignore_file = os.path.join(INPUT_DIR, self.name + '.ignore')
        if os.path.exists(ignore_file):
            with open(ignore_file) as fh:
                ignore_reason = fh.read()

            pytest.skip(ignore_reason)

        # if '.depends' file is present, check if all dependencies are
        # satisfied, otherwise skip test

        depends_file = os.path.join(INPUT_DIR, self.name + '.depends')
        if os.path.exists(depends_file):
            with open(depends_file) as fh:
                for line in fh:
                    dep = line.rstrip('\n')
                    try:
                        if not check_dependency[dep]():
                            pytest.skip("Unmet dependency for test: %s" % line)
                    except KeyError:
                        pytest.skip("Unknown test dependency: %s" % line)

        # run the actual test

        retcode, output = self._build()

        # verify results

        retcode_file = os.path.join(INPUT_DIR, self.name + '.retcode')
        if os.path.exists(retcode_file):
            with open(retcode_file) as f:
                first_line = f.readline()
                expected_retcode = int(first_line)
                if expected_retcode == retcode:
                    return
                else:
                    self._fail(
                        'Exit code of %d did not match expected %d'
                        % (retcode, expected_retcode),
                        output,
                    )
        elif retcode > 0:
            self._fail('Call failed with %d' % retcode, output)

        no_pdf = os.path.exists(os.path.join(INPUT_DIR, self.name + '.nopdf'))
        if no_pdf:
            return

        output_file = os.path.join(OUTPUT_DIR, self.name + '.pdf')
        reference_file = os.path.join(REFERENCE_DIR, self.name + '.pdf')

        if not os.path.exists(reference_file):
            self._fail(
                'No reference file at %r to compare against.'
                % (os.path.relpath(output_file, ROOT_DIR),),
            )

        if os.path.isdir(output_file):
            if not os.path.isdir(reference_file):
                self._fail(
                    'Mismatch between type of output (directory) and '
                    'reference (file)',
                    output,
                )
            output_files = glob.glob(os.path.join(output_file, '*.pdf'))
            reference_files = glob.glob(os.path.join(reference_file, '*.pdf'))
        else:
            if not os.path.isfile(reference_file):
                self._fail(
                    'Mismatch between type of output (file) and reference '
                    '(directory)',
                    output,
                )
            output_files = [output_file]
            reference_files = [reference_file]

        if len(reference_files) != len(output_files):
            self._fail(
                'Mismatch between number of files expected and generated',
                output,
            )

        reference_files.sort()
        output_files.sort()

        for ref_pdf, out_pdf in zip(reference_files, output_files):
            try:
                compare_pdfs(ref_pdf, out_pdf)
            except AssertionError as exc:
                raise CompareException(exc)

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, CompareException):
            return excinfo.exconly()

        return super(Item, self).repr_failure(excinfo)

    def reportinfo(self):
        return self.fspath, 0, self.name


class RstItem(Item):
    def _build(self):
        input_ref = self.name + '.rst'
        output_pdf = os.path.join(OUTPUT_DIR, self.name + '.pdf')
        output_log = os.path.join(OUTPUT_DIR, self.name + '.log')

        for path in (output_log, output_pdf):
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

        cmd = ['rst2pdf', '--lang', 'en', '--date-invariant', '-v', input_ref]

        cli_file = os.path.join(INPUT_DIR, self.name + '.cli')
        if os.path.exists(cli_file):
            with open(cli_file) as fh:
                cmd += shlex.split(fh.read())

        style_file = os.path.join(INPUT_DIR, self.name + '.yaml')
        if os.path.exists(style_file):
            cmd += ['-s', os.path.basename(style_file)]

        if '-o' not in cmd:
            cmd += ['-o', output_pdf]

        try:
            output = subprocess.check_output(
                cmd,
                cwd=INPUT_DIR,
                stderr=subprocess.STDOUT,
            )
            retcode = 0
        except subprocess.CalledProcessError as exc:
            output = exc.output
            retcode = exc.returncode

        with open(output_log, 'wb') as fh:
            fh.write(output)

        expected_log_file = os.path.join(
            os.path.join(INPUT_DIR, self.name + '.expected_log')
        )
        output_file = os.path.join(OUTPUT_DIR, self.name + '.pdf')
        no_pdf = os.path.exists(os.path.join(INPUT_DIR, self.name + '.nopdf'))

        if os.path.exists(expected_log_file):
            # look for each line in expected_log_file within the output log
            output_string = output.decode("utf-8")
            with open(expected_log_file) as expected_log_file:
                for message in expected_log_file:
                    message = message.strip()
                    if message and message not in output_string:
                        self._fail(
                            'Log message %s was not found' % message,
                            output,
                        )
            if no_pdf:
                # As we are looking for a log entry, we ignore any created pdf file if a .nopdf
                # file exists. That is, it doesn't matter if the file was created or not.
                return retcode, output

        if not os.path.exists(output_file) and not no_pdf:
            self._fail(
                'File %r was not generated' % (os.path.relpath(output_file, ROOT_DIR),),
                output,
            )
        elif os.path.exists(output_file) and no_pdf:
            self._fail(
                'File %r was erroneously generated'
                % (os.path.relpath(output_file, ROOT_DIR),),
                output,
            )

        return retcode, output


class SphinxItem(Item):
    def _build(self):
        __tracebackhide__ = True

        output_pdf = os.path.join(OUTPUT_DIR, self.name + '.pdf')
        output_log = os.path.join(OUTPUT_DIR, self.name + '.log')

        for path in (output_log, output_pdf):
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

        input_dir = os.path.join(INPUT_DIR, self.name)
        build_dir = tempfile.mkdtemp(prefix='rst2pdf-sphinx-')

        cmd = ['sphinx-build', '-b', 'pdf', input_dir, build_dir]

        try:
            output = subprocess.check_output(
                cmd,
                cwd=INPUT_DIR,
                stderr=subprocess.STDOUT,
            )
            retcode = 0
        except subprocess.CalledProcessError as exc:
            output = exc.output
            retcode = exc.returncode

        with open(output_log, 'wb') as fh:
            fh.write(output)

        pdf_files = glob.glob(os.path.join(build_dir, '*.pdf'))
        if pdf_files:
            if len(pdf_files) == 1:
                shutil.copyfile(pdf_files[0], output_pdf)
            else:
                shutil.copytree(build_dir, output_pdf)
        else:
            self._fail('Output PDF not generated', output)

        shutil.rmtree(build_dir)

        return retcode, output


class CompareException(Exception):
    """Custom exception for error reporting."""


def pytest_collect_file(file_path, parent):

    parent_directory = file_path.parents[0]
    if "input" not in str(parent_directory):
        return

    parent_dir = os.path.split(parent_directory)[-1]

    if file_path.suffix == '.rst' and parent_dir == 'input':
        return RstFile.from_parent(parent=parent, path=file_path)
    elif file_path.name == 'conf.py' and parent_dir.startswith('sphinx'):
        return SphinxFile.from_parent(parent=parent, path=file_path)


collect_ignore = ['tests/input/*.py']
