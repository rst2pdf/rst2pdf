#!/usr/bin/env python
# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

'''
Quick confidence test for rst2pdf.
'''

import autotest

cmdline = '''
          -f

          input/test_issue_103.txt
          input/test_issue_175.txt

'''.split()

if __name__ == '__main__':
    import sys
    assert len(sys.argv) == 1, 'confidence test does not accept command line arguments'
    autotest.main(cmdline)
