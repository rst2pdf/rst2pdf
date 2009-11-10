# -*- coding: utf-8 -*-

from autotest import MD5Info, PathInfo, globjoin
from autotest import run_single

import sys, os
import nose.plugins.skip

class RunTest:
    def __init__(self,f):
        basename = os.path.basename(f)
        self.description = basename 
        mprefix = os.path.join(PathInfo.md5dir, basename)[:-4]
        md5file = mprefix + '.json'
        info=MD5Info()
        if os.path.exists(md5file):
            f = open(md5file, 'rb')
            exec f in info
            f.close()
        if info.good_md5 in [[],['sentinel']]:
            # This is an open issue or something that can't be checked automatically
            self.skip=True
        else:
            self.skip=False
    def __call__(self,f):
        if self.skip:
            raise nose.plugins.skip.SkipTest
        else:
            key, errcode = run_single(f)
            if key in ['incomplete']:
                raise nose.plugins.skip.SkipTest
            assert key == 'good', '%s is not good: %s'%(f,key)

def test():
    testfiles = globjoin(PathInfo.inpdir, '*.txt')
    results = {}
    for fname in testfiles:
        yield RunTest(fname), fname

def setup():
    PathInfo.add_coverage()
