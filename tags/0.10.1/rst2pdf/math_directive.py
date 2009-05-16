# -*- coding: utf-8 -*-

from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils.nodes import General, Inline, Element
from docutils.parsers.rst import roles


if 'Directive' in rst.__dict__:


    class Math(rst.Directive):

        has_content = True

        def run(self):
            return [math_node(data=''.join(self.content), rawsource=''.join(self.content))]

        def __repr__(self):
            return u''.join(self.content)

else:


    def Math(name, arguments, options, content, lineno,
            content_offset, block_text, state, state_machine):
        return [math_node(data=''.join(content), rawsource=''.join(content))]

    Math.content = True


directives.register_directive('math', Math)


class math_node(General, Inline, Element):

    children = ()

    def __init__(self, rawsource='', *children, **attributes):
        self.rawsource = rawsource
        self.math_data = attributes['data']
        Element.__init__(self, rawsource, *children, **attributes)



def math_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    return [math_node(rawtext[7:-1], data=rawtext[7:-1])], []


roles.register_local_role('math', math_role)
