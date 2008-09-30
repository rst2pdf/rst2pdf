# -*- coding: utf-8 -*-
#$HeadURL: https://rst2pdf.googlecode.com/svn/trunk/rst2pdf/tests/test_include.py $
#$LastChangedDate: 2008-08-29 16:09:08 +0200 (Fri, 29 Aug 2008) $
#$LastChangedRevision: 160 $
from unittest import TestCase, makeSuite

from docutils.core import publish_doctree
import rst2pdf
#import pdb; pdb.set_trace()

from os.path import join
from utils import PREFIX

import pdb


def input_file_path(file):
    """ unused here
    is looked for in tests below
    where am I"""
    return join(PREFIX, file)

class IncludeTests(TestCase):
    def test_wrong_file(self):
        input="""
This one gives a warning, non existent file:

.. code-block:: python
   :include: xyzzy.py
"""
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.astext(), u'\n')
        
    def test_missing_file(self):
        input="""
This one gives a warning, missing file:

.. code-block:: python
   :include:
"""
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'system_message')
        self.assertEqual(include.children[1].tagname, 'literal_block')
        self.assertEqual(include.children[1].astext(), u'.. code-block:: python\n   :include:')

    def test_existing_file(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
""" % input_file_path('test_include.py')
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.children[0].astext(), u'# -*- coding: utf-8 -*-')

    def test_wrong_lang(self):
        input="""
This one exists:

.. code-block:: nothing
   :include: %s
""" % input_file_path('test_include.py')
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.astext().split('\n')[0], u'# -*- coding: utf-8 -*-')

    def test_existing_file_start_at(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
   :start-at: def input_file_path(file):
""" % input_file_path('test_include.py')
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.astext().split('\n')[0], u'def input_file_path(file):')
        self.assertEqual(include.astext().split('\n')[-2:][0], u"    unittest.main(defaultTest='test_suite')")
        
    def test_existing_file_start_after(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
   :start-after: def input_file_path(file):
""" % input_file_path('test_include.py')
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.astext().split('\n')[0], u'    """ unused here')
        self.assertEqual(include.astext().split('\n')[-2:][0], u"    unittest.main(defaultTest='test_suite')")
        
    def test_existing_file_end_before(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
   :end-before: return join(PREFIX, file)
""" % input_file_path('test_include.py')
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.children[0].astext(), u'# -*- coding: utf-8 -*-')
        self.assertEqual(include.astext().split('\n')[-3:][0], u'    where am I"""')
        
    def test_existing_file_end_at(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
   :end-at: def input_file_path(file):
""" % input_file_path('test_include.py')
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.children[0].astext(), u'# -*- coding: utf-8 -*-')
        self.assertEqual(include.astext().split('\n')[-2:][0], u'def input_file_path(file):')
        
    def test_existing_file_start_at_end_at(self):
        input="""
This one exists:

.. code-block:: py
   :include: %s
   :start-at: def input_file_path(file):
   :end-at: return join(PREFIX, file)
""" % input_file_path('test_include.py')
        doctree=publish_doctree(input)
        include = doctree.children[1]
        self.assertEqual(include.tagname, 'literal_block')
        self.assertEqual(include.astext().split('\n')[0], u'def input_file_path(file):')
        self.assertEqual(include.astext().split('\n')[-2:][0], u"    return join(PREFIX, file)")
        
        
def test_suite():
    suite = makeSuite(IncludeTests)
    return suite
    
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
