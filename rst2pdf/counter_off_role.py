# -*- coding: utf-8 -*-

from docutils.nodes import Text, target

def counter_fn(name, rawtext, text, lineno, inliner, options={}, content=[]):
    return [], []

counter_fn.content=False

from docutils.parsers.rst import roles
roles.register_canonical_role('counter', counter_fn)
