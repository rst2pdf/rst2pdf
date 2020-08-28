#!/usr/bin/env python3
# -*- coding: utf8 -*-
# :Copyright: © 2015 Günter Milde.
# :License: Released under the terms of the `2-Clause BSD license`_, in short:
#
#    Copying and distribution of this file, with or without modification,
#    are permitted in any medium without royalty provided the copyright
#    notice and this notice are preserved.
#    This file is offered as-is, without any warranty.
#
# .. _2-Clause BSD license: http://www.spdx.org/licenses/BSD-2-Clause

"""
A version of rst2html5 with support for rst2pdf's custom roles/directives.
"""

import locale

from docutils.core import default_description
from docutils.core import publish_cmdline
from docutils.parsers.rst import directives

from rst2pdf.directives import code_block
from rst2pdf.directives import noop
from rst2pdf.roles import counter_off  # noqa
from rst2pdf.roles import package  # noqa


locale.setlocale(locale.LC_ALL, '')

directives.register_directive('code-block', code_block.code_block_directive)
directives.register_directive('oddeven', noop.noop_directive)

description = (
    'Generates HTML5 documents from standalone reStructuredText '
    'sources.\n' + default_description
)

publish_cmdline(writer_name='html5', description=description)
