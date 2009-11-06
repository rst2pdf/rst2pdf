# -*- coding: utf-8 -*-

from autotest import PathInfo, run_single_test, globjoin

import sys

class RunTest:
    def __init__(self,f):
        sys.stdout.write(f)
        sys.stdout.flush()
        self.description = f
        
    def __call__(self,f):
        key, errcode = run_single_test(self.description)
        assert key == 'good', '%s is not good'%f

def test():
    testfiles = globjoin(PathInfo.inpdir, '*.txt')
    results = {}
    for fname in testfiles[-5:]:
        yield RunTest(fname), fname
