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
        ignfile = os.path.join(PathInfo.inpdir , basename[:-4])+'.ignore'
        info=MD5Info()
        self.skip=False
        self.openIssue=False
        if os.path.exists(ignfile):
            self.skip=True
        if os.path.exists(md5file):
            f = open(md5file, 'rb')
            exec f in info
            f.close()
        if info.good_md5 in [[],['sentinel']]:
            # This is an open issue or something that can't be checked automatically
            self.openIssue=True
            
    def __call__(self,f):
        if self.skip:
            raise nose.plugins.skip.SkipTest
        elif self.openIssue:
            assert False, 'Test has no known good output (Open Issue)'
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
