#!/usr/bin/env python3

"""
A minimal front end to the Docutils Publisher, producing HTML.
"""

import locale

from docutils.core import publish_cmdline, default_description
from docutils.parsers.rst import directives
from docutils.parsers.rst import roles

from rst2pdf.directives import code_block
from rst2pdf.directives import noop
from rst2pdf.roles import counter_off


locale.setlocale(locale.LC_ALL, '')

directives.register_directive('code-block', code_block.code_block_directive)
directives.register_directive('oddeven', noop.noop_directive)
roles.register_canonical_role('counter', counter_off.counter_fn)

description = (
    'Generates (X)HTML documents from standalone reStructuredText '
    'sources.  ' + default_description
)

publish_cmdline(writer_name='html', description=description)
