# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: BSD
#
# Copyright (c) 2009 by Leandro Lucarella, Roberto Alsina

from docutils.nodes import Element, literal_block
from docutils.parsers import rst
from docutils.parsers.rst import directives
from reportlab.graphics import renderPDF

from .log import log

try:
    import aafigure
    import aafigure.pdf
except ImportError:
    aafigure = None

WARNED = False


class Aanode(Element):
    children = ()

    def __init__(self, content, options, rawsource='', *children, **attributes):
        self.content = content
        self.options = options
        Element.__init__(self, rawsource, *children, **attributes)

    def copy(self, **attributes):
        return Aanode(self.content, self.options, **self.attributes)

    def gen_flowable(self, style_options):
        options = dict(style_options)
        # explicit :option: always precedes
        options.update(self.options)
        visitor = aafigure.process(
            '\n'.join(self.content), aafigure.pdf.PDFOutputVisitor, options=options
        )
        return renderPDF.GraphicsFlowable(visitor.drawing)


class Aafig(rst.Directive):
    """
    Directive to insert an ASCII art figure to be rendered by aafigure.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = dict(
        scale=float,
        line_width=float,
        background=str,
        foreground=str,
        fill=str,
        name=str,
        aspect=float,
        textual=directives.flag,
        proportional=directives.flag,
    )

    def run(self):
        global WARNED
        if 'textual' in self.options:
            self.options['textual'] = True
        if 'proportional' in self.options:
            self.options['proportional'] = True
        if aafigure is not None:
            return [Aanode(self.content, self.options)]
        if not WARNED:
            log.error(
                'To render the aafigure directive correctly, please install aafigure'
            )
            WARNED = True
        return [literal_block(text='\n'.join(self.content))]


directives.register_directive('aafig', Aafig)
directives.register_directive('aafigure', Aafig)
