#!/usr/bin/env python

import shutil
import subprocess
import tempfile

from pathlib import Path

from PIL import Image

root = Path('testcases')

for folder in sorted(root.iterdir()):
    print('PROCESSING %s' % folder.name)
    output = folder / 'output.pdf'
    expected = folder / 'expected_output.pdf'

    if not output.exists():
        print(' SKIPPING: missing output.pdf')
    elif not expected.exists():
        print(' SKIPPING: missing expected_output.pdf')
    else:
        with tempfile.TemporaryDirectory() as tmp:
            tmpp = Path(tmp)
            conv = ['convert', '-density', '96x96']
            subprocess.call(conv + [str(output), str(tmpp / 'outputp.png')])
            subprocess.call(conv + [str(expected), str(tmpp / 'exp_outputp.png')])
            c_output = len(list(tmpp.glob('outputp*.png')))
            c_expected = len(list(tmpp.glob('exp_outputp*.png')))
            errors = False
            if c_output != c_expected:
                print('  Page count mismatch: %d != %d' % (c_output, c_expected))
            else:
                for outpage in tmpp.glob('outputp*.png'):
                    exppage = tmpp / ('exp_%s' % outpage.name)
                    diffpage = tmpp / ('diff_%s.png' % outpage.name)
                    cmds = [
                        'compare',
                        '-metric', 'PSNR',
                        str(outpage),
                        str(exppage),
                        str(diffpage)
                    ]
                    try:
                        result = subprocess.check_output(cmds, stderr=subprocess.STDOUT)
                    except subprocess.CalledProcessError as err:
                        result = err.output
                    if result != b'inf':
                        print("  Page '%s' has errors" % outpage.name)
                        errors = True
                        img = Image.open(str(diffpage))
                        img.show()
            if errors:
                replace = input('Replace expected output? ')
                if replace.lower() == 'y':
                    shutil.copy(str(output), str(expected))
                elif replace.lower() == 'q':
                    exit(0)
