# -*- coding: utf-8 -*-

from docutils.nodes import Text, target
from docutils.parsers.rst import roles

values = {}


class CounterNode(Text):
    children = ()

    def __init__(self, data, rawsource=''):
        if ':' in data:
            self.name, value = [s.lower() for s in data.split(':')][:2]
            self.value = int(value)
        else:
            self.name = data.lower()
            self.value = values.get(self.name, 1)
        values[self.name] = self.value + 1

    def astext(self):
        return str(self.value)


def counter_fn(name, rawtext, text, lineno, inliner, options={}, content=[]):
    n = CounterNode(text)
    s = '%s-%s' % (n.name, n.value)
    return [target(ids=[s]), n], []


counter_fn.content = True

roles.register_canonical_role('counter', counter_fn)
