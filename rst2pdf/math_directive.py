# -*- coding: utf-8 -*-

from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils.nodes import General,Inline,Element
from docutils.parsers.rst import roles

class Math(rst.Directive):
    has_content = True
    def run(self):
        # Raise an error if the directive does not have contents.
        #self.assert_has_content()
        return [ math_node(''.join(self.content),''.join(self.content)) ]
    def __repr__(self):
        return u''.join(self.content)

class math_node(General,Inline,Element):
    children = ()
    def __init__(self,data='',rawsource='',*children, **attributes):
       self.rawsource=rawsource
       self.math_data=data
       Element.__init__(self,rawsource,*children, **attributes)
 
directives.register_directive('math', Math)