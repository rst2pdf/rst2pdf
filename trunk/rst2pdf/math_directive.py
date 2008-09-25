# -*- coding: utf-8 -*-

from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils.nodes import Text

class Math(rst.Directive):
    has_content = True
    def run(self):
        # Raise an error if the directive does not have contents.
        self.assert_has_content()
        return [ math_node(''.join(self.content),''.join(self.content)) ]

class math_node(Text):
    def __init__(self,data,rawsource):
        self.rawsource=rawsource
        self.math_data=data
        Text.__init__(self,data)

directives.register_directive('math', Math)
