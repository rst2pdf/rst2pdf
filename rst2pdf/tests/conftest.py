"""
Copyright (c) 2020, Stephen Finucane <stephen@that.guru>

Automated testing for rst2pdf.

See LICENSE.txt for licensing terms
"""

import glob
import hashlib
import os
import shlex
import shutil
import subprocess
import tempfile

from packaging import version
import pytest
import six


ROOT_DIR = os.path.realpath(os.path.dirname(__file__))
INPUT_DIR = os.path.join(ROOT_DIR, 'input')
OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
MD5_DIR = os.path.join(ROOT_DIR, 'md5')


class MD5Info(dict):
    """Round-trip good, bad, unknown information to/from a .json file.

    For formatting reasons, the json module isn't used for writing, and since
    we're not worried about security, we don't bother using it for reading,
    either.
    """

    # Category to dump new data into
    new_category = 'unknown'
    # Categories which always should be in file
    mandatory_categories = ['good', 'bad']

    # Sentinel to make manual changes and diffs easy
    sentinel = 'sentinel'
    # An empty list is one which is truly empty or which has a sentinel
    empty = [[], ['sentinel']]
    # Suffix for file items
    suffix = '_md5'

    def __init__(self):
        self.__dict__ = self
        self.changed = False
        for name in self.mandatory_categories:
            setattr(self, name + self.suffix, [self.sentinel])

    def __str__(self):
        """Return the string to output to the MD5 file."""
        result = []

        for name, value in sorted(self.items()):
            if not name.endswith(self.suffix):
                continue

            result.append('%s = [' % name)
            result.append(
                ',\n'.join(["        '%s'" % item for item in sorted(value)])
            )
            result.append(']\n')

        result.append('')
        return '\n'.join(result)

    def find(self, checksum, new_category=new_category):
        """Find the given checksum.

        find() has some serious side-effects. If the checksum is found, the
        category it was found in is returned. If the checksum is not found,
        then it is automagically added to the unknown category. In all cases,
        the data is prepped to output to the file (if necessary), and
        self.changed is set if the data is modified during this process.
        Functional programming this isn't...

        A quick word about the 'sentinel'. This value starts with an 's',
        which happens to sort > highest hexadecimal digit of 'f', so it is
        always a the end of the list.

        The only reason for the sentinel is to make the database either to work
        with. Both to modify (by moving an MD5 line from one category to
        another) and to diff. This is because every hexadecimal line (every
        line except the sentinel) is guaranteed to end with a comma.
        """
        suffix = self.suffix
        new_key = new_category + suffix
        sentinel = set([self.sentinel])

        # Create a dictionary of relevant current information
        # in the database.
        oldinfo = {k: v for k, v in self.items() if k.endswith(suffix)}

        # Create sets and strip the sentinels while
        # working with the dictionary.
        newinfo = {k: set(v) - sentinel for k, v in oldinfo.items()}

        # Create an inverse mapping of MD5s to key names
        inverse = {}
        for key, values in newinfo.items():
            for value in values:
                inverse.setdefault(value, set()).add(key)

        # In general, inverse should be a function (there
        # should only be one answer to the question "What
        # key name goes with this MD5?")   If not,
        # either report an error, or just remove one of
        # the possible answers if it is the same answer
        # we give by default.
        for value, keys in inverse.items():
            if len(keys) > 1 and new_key in keys:
                keys.remove(new_key)
                newinfo[new_key].remove(value)

            if len(keys) > 1:
                raise SystemExit(
                    'MD5 %s is stored in multiple categories: %s' % (
                        value, ', '.join(keys),
                    )
                )

        # Find the result in the dictionary.  If it's not
        # there we have to add it.
        result, = inverse.get(checksum, [new_key])
        if result == new_key:
            newinfo.setdefault(result, set()).add(checksum)

        # Create a canonical version of the dictionary,
        # by adding sentinels and sorting the results.
        for key, value in newinfo.items():
            newinfo[key] = sorted(value | sentinel)

        # See if we changed anything
        if newinfo != oldinfo:
            self.update(newinfo)
            self.changed = True

        # And return the key associated with the MD5
        assert result.endswith(suffix), result

        return result[:-len(suffix)]


class File(pytest.File):

    if version.parse(pytest.__version__) < version.parse('5.4.0'):
        @classmethod
        def from_parent(cls, parent, fspath):
            return cls(parent=parent, fspath=fspath)


class TxtFile(File):

    def collect(self):
        name = os.path.splitext(self.fspath.basename)[0]
        yield TxtItem.from_parent(parent=self, name=name)


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

    def runtest(self):
        # if '.ignore' file present, skip test

        ignore_file = os.path.join(INPUT_DIR, self.name + '.ignore')
        if os.path.exists(ignore_file):
            with open(ignore_file) as fh:
                ignore_reason = fh.read()

            pytest.skip(ignore_reason)

        # load MD5 info

        info = MD5Info()

        md5_file = os.path.join(MD5_DIR, self.name + '.json')
        if os.path.exists(md5_file):
            with open(md5_file, 'rb') as fh:
                six.exec_(fh.read(), info)

        # if we have a PDF file output, we must have a MD5 checksum stored

        no_pdf = os.path.exists(os.path.join(INPUT_DIR, self.name + '.nopdf'))

        if info.good_md5 in ([], ['sentinel']) and not no_pdf:
            pytest.fail(
                'Test has no known good output (open issue)',
                pytrace=False,
            )

        # run the actual test

        retcode, output = self._build()

        # verify results

        if retcode:
            pytest.fail(
                'Call failed with %d:\n\n%s' % (retcode, output),
                pytrace=False,
            )

        if no_pdf:
            return

        output_file = os.path.join(OUTPUT_DIR, self.name + '.pdf')
        if os.path.isdir(output_file):
            output_files = list(glob.glob(os.path.join(output_file, '*.pdf')))
        else:
            output_files = [output_file]

        hashes = []
        for output_file in output_files:
            with open(output_file, 'rb') as fh:
                m = hashlib.md5()
                m.update(fh.read())
                hashes.append(m.hexdigest())

        result_type = info.find(' '.join(hashes), '')

        if result_type == 'bad':
            pytest.fail('Generated a known bad checksum', pytrace=False)

        if not result_type:
            pytest.fail(
                "Couldn't find a matching checksum for %s" % ' '.join(hashes),
                pytrace=False,
            )

    def reportinfo(self):
        return self.fspath, 0, self.name


class TxtItem(Item):

    def _build(self):
        input_ref = self.name + '.txt'
        output_pdf = os.path.join(OUTPUT_DIR, self.name + '.pdf')
        output_log = os.path.join(OUTPUT_DIR, self.name + '.log')

        for path in (output_log, output_pdf):
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

        cmd = ['rst2pdf', '--date-invariant', '-v', input_ref]

        cli_file = os.path.join(INPUT_DIR, self.name + '.cli')
        if os.path.exists(cli_file):
            with open(cli_file) as fh:
                cmd += shlex.split(fh.read())

        style_file = os.path.join(INPUT_DIR, self.name + '.style')
        if os.path.exists(style_file):
            cmd += ['-s', os.path.basename(style_file)]

        cmd += ['-o', output_pdf]

        try:
            output = subprocess.check_output(
                cmd, cwd=INPUT_DIR, stderr=subprocess.STDOUT,
            )
            retcode = 0
        except subprocess.CalledProcessError as exc:
            output = exc.output
            retcode = exc.returncode

        with open(output_log, 'wb') as fh:
            fh.write(output)

        output_file = os.path.join(OUTPUT_DIR, self.name + '.pdf')
        no_pdf = os.path.exists(os.path.join(INPUT_DIR, self.name + '.nopdf'))
        if not os.path.exists(output_file):
            assert no_pdf, 'File %s not generated' % os.path.basename(
                output_file
            )

        return retcode, output


class SphinxItem(Item):

    def _build(self):
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
                cmd, cwd=INPUT_DIR, stderr=subprocess.STDOUT,
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
            pytest.fail('Output PDF not generated', pytrace=False)

        return retcode, output


def pytest_collect_file(parent, path):
    if not (path.fnmatch('*/input') or path.fnmatch('*/input/*')):
        return

    parent_dir = os.path.split(path.dirname)[-1]

    if path.ext == '.txt' and parent_dir == 'input':
        return TxtFile.from_parent(parent=parent, fspath=path)
    elif path.basename == 'conf.py' and parent_dir.startswith('sphinx'):
        return SphinxFile.from_parent(parent=parent, fspath=path)


collect_ignore = ['rst2pdf/tests/input/*.py']
