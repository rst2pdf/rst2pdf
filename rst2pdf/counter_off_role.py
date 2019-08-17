# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: MIT

from docutils.nodes import Text, target
from docutils.parsers.rst import roles


def counter_fn(name, rawtext, text, lineno, inliner, options={}, content=[]):
    return [], []


counter_fn.content = False

roles.register_canonical_role('counter', counter_fn)
