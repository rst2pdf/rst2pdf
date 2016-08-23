# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from docutils.nodes import Text, target

values = {}


class CounterNode(Text):
    children = ()
    def __init__(self, data, rawsource=''):
        if ':' in data:
            self.name, value = [s.lower() for s in data.split(':')][:2]
            self.value=int(value)
        else:
            self.name=data.lower()
            self.value=values.get(self.name,1)
        values[self.name]=self.value+1
        
    def astext(self):
        return str(self.value)

def counter_fn(name, rawtext, text, lineno, inliner, options={}, content=[]):
    n=CounterNode(text)
    s='%s-%s'%(n.name, n.value)
    return [target(ids=[s]),n], []

counter_fn.content=True

from docutils.parsers.rst import roles
roles.register_canonical_role('counter', counter_fn)
