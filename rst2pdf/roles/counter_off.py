# -*- coding: utf-8 -*-

from docutils.parsers.rst import roles


def counter_fn(name, rawtext, text, lineno, inliner, options={}, content=[]):
    return [], []


counter_fn.content = False

roles.register_canonical_role('counter', counter_fn)
