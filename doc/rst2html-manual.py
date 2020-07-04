#!/usr/bin/python

# $Id: rst2html.py 4564 2006-05-21 20:44:42Z wiemann $
# Author: David Goodger <goodger@python.org>
# Copyright: This module has been placed in the public domain.

"""
A minimal front end to the Docutils Publisher, producing HTML.
"""

try:
    import locale

    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_cmdline, default_description
from docutils.parsers.rst import directives
import rst2pdf.pygments_code_block_directive

directives.register_directive(
    'code-block', rst2pdf.pygments_code_block_directive.code_block_directive
)

from docutils.parsers.rst import roles
import rst2pdf.counter_off_role

roles.register_canonical_role('counter', rst2pdf.counter_off_role.counter_fn)

import rst2pdf.noop_directive

directives.register_directive('oddeven', rst2pdf.noop_directive.noop_directive)

description = (
    'Generates (X)HTML documents from standalone reStructuredText '
    'sources.  ' + default_description
)

publish_cmdline(writer_name='html', description=description)
