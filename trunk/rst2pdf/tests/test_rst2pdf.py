# -*- coding: utf-8 -*-
import unittest

class InstallTests(unittest.TestCase):

    def testexample(self):
        pass
        
def test_suite():
    return unittest.makeSuite(InstallTests)
    
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
