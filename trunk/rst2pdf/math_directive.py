# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

from docutils.parsers import rst
from docutils.parsers.rst import directives
from docutils.nodes import General, Inline, Element
from docutils.parsers.rst import roles

import basenodehandler, math_flowable

if 'Directive' in rst.__dict__:

    class Math(rst.Directive):
        has_content = True

        def run(self):
            return [math_node(data=''.join(self.content),
                              rawsource=''.join(self.content))]

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

class HandleMath(basenodehandler.NodeHandler, math_node):
    def gather_elements(self, client, node, style):
        return [math_flowable.Math(node.math_data)]

    def get_text(self, client, node, replaceEnt):
        mf = math_flowable.Math(node.math_data)
        w, h = mf.wrap(0, 0)
        descent = mf.descent()
        img = mf.genImage()
        client.to_unlink.append(img)
        return '<img src="%s" width=%f height=%f valign=%f/>' % (
            img, w, h, -descent)

