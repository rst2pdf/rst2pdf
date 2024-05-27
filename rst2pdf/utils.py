# -*- coding: utf-8 -*-
# See LICENSE.txt for licensing terms

import shlex

import jinja2
from reportlab.lib.colors import Color
from reportlab.platypus.flowables import CondPageBreak

from . import flowables
from .log import log, nodeid
from .styles import adjustUnits

PageCounter = None


def parseRaw(data, node):
    """Parse and process a simple DSL to handle creation of flowables.

    Supported (can add others on request):

    * PageBreak [<template name>] [background={img_filename.jpg}] [background_fit_mode={mode (e.g. stretch)}]
    * EvenPageBreak
    * OddPageBreak
    * FrameBreak
    * Spacer width, height
    * Transition
    * SetPageCounter
    * TextAnnotation "text of annotation" x_begin=-1 y_begin=-1 x_end=-1 y_end=-1

    """
    global PageCounter
    if PageCounter is None:
        from rst2pdf.createpdf import PageCounter as pc

        PageCounter = pc

    elements = []
    lines = data.splitlines()
    for line in lines:
        lexer = shlex.shlex(line, punctuation_chars=True)
        lexer.whitespace += ','
        tokens = list(lexer)
        if not tokens:
            continue  # Empty line
        command = tokens[0]
        if command == 'PageBreak':
            if len(tokens) == 1:
                elements.append(flowables.MyPageBreak())
            else:
                elements.append(flowables.MyPageBreak(tokens[1:]))
        elif command == 'EvenPageBreak':
            if len(tokens) == 1:
                elements.append(flowables.MyPageBreak(breakTo='even'))
            else:
                elements.append(flowables.MyPageBreak(tokens[1:], breakTo='even'))
        elif command == 'OddPageBreak':
            if len(tokens) == 1:
                elements.append(flowables.MyPageBreak(breakTo='odd'))
            else:
                elements.append(flowables.MyPageBreak(tokens[1:], breakTo='odd'))
        elif command == 'FrameBreak':
            if len(tokens) == 1:
                elements.append(CondPageBreak(99999))
            else:
                elements.append(CondPageBreak(float(tokens[1])))
        elif command == 'Spacer':
            elements.append(
                flowables.MySpacer(adjustUnits(tokens[1]), adjustUnits(tokens[2]))
            )
        elif command == 'Transition':
            elements.append(flowables.Transition(*tokens[1:]))
        elif command == 'SetPageCounter':
            elements.append(PageCounter(*tokens[1:]))
        elif command == 'TextAnnotation':
            elements.append(flowables.TextAnnotation(*tokens[1:]))
        else:
            log.error(
                'Unknown command %s in raw pdf directive [%s]' % (command, nodeid(node))
            )
    return elements


HAS_XHTML2PDF = True
try:
    import xhtml2pdf.default  # NOQA
    from xhtml2pdf.util import COLOR_BY_NAME
    from xhtml2pdf.util import Memoized as memoized
    from xhtml2pdf.context import pisaContext
    from xhtml2pdf.parser import pisaGetAttributes
    from xhtml2pdf.document import pisaStory
    import xhtml2pdf.parser as pisa_parser
except ImportError:
    try:
        from sx.pisa3.pisa_util import COLOR_BY_NAME

        def memoized(*a):
            return a

        from sx.pisa3.pisa_context import pisaContext
        from sx.pisa3.pisa_parser import pisaGetAttributes
        from sx.pisa3.pisa_document import pisaStory
        import sx.pisa3.pisa_parser as pisa_parser
    except ImportError:
        HAS_XHTML2PDF = False


if HAS_XHTML2PDF:

    COLOR_BY_NAME['initial'] = Color(0, 0, 0)

    from xml.dom import Node

    def pisaPreLoop2(node, context, collect=False):
        """
        Collect all CSS definitions
        """

        data = u""
        if node.nodeType == Node.TEXT_NODE and collect:
            data = node.data

        elif node.nodeType == Node.ELEMENT_NODE:
            name = node.tagName.lower()

            # print name, node.attributes.items()
            if name in ("style", "link"):
                attr = pisaGetAttributes(context, name, node.attributes)
                print(" ", attr)
                media = [x.strip() for x in attr.media.lower().split(",") if x.strip()]
                # print repr(media)

                if attr.get("type", "").lower() in ("", "text/css") and (
                    not media or "all" in media or "print" in media or "pdf" in media
                ):

                    if name == "style":
                        for node in node.childNodes:
                            data += pisaPreLoop2(node, context, collect=True)
                        return u""

                    if (
                        name == "link"
                        and attr.href
                        and attr.rel.lower() == "stylesheet"
                    ):
                        context.addCSS(
                            '\n@import "%s" %s;' % (attr.href, ",".join(media))
                        )

        for node in node.childNodes:
            result = pisaPreLoop2(node, context, collect=collect)
            if collect:
                data += result

        return data

    pisa_parser.pisaPreLoop = pisaPreLoop2

    HTML_CSS = """
    html {
        font-family: Helvetica;
        font-size: 7px;
        font-weight: normal;
        color: #000000;
        background-color: transparent;
        margin: 0;
        padding: 0;
        line-height: 150%;
        border: 1px none;
        display: inline;
        width: auto;
        height: auto;
        white-space: normal;
    }

    b,
    strong {
        font-weight: bold;
    }

    i,
    em {
        font-style: italic;
    }

    u {
        text-decoration: underline;
    }

    s,
    strike {
        text-decoration: line-through;
    }

    a {
        text-decoration: underline;
        color: blue;
    }

    ins {
        color: green;
        text-decoration: underline;
    }
    del {
        color: red;
        text-decoration: line-through;
    }

    pre,
    code,
    kbd,
    samp,
    tt {
        font-family: "Courier New";
    }

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        font-weight:bold;
        -pdf-outline: true;
        -pdf-outline-open: false;
    }

    h1 {
        /*18px via YUI Fonts CSS foundation*/
        font-size:138.5%;
        -pdf-outline-level: 0;
    }

    h2 {
        /*16px via YUI Fonts CSS foundation*/
        font-size:123.1%;
        -pdf-outline-level: 1;
    }

    h3 {
        /*14px via YUI Fonts CSS foundation*/
        font-size:108%;
        -pdf-outline-level: 2;
    }

    h4 {
        -pdf-outline-level: 3;
    }

    h5 {
        -pdf-outline-level: 4;
    }

    h6 {
        -pdf-outline-level: 5;
    }

    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    p,
    pre,
    hr {
        margin:1em 0;
    }

    address,
    blockquote,
    body,
    center,
    dl,
    dir,
    div,
    fieldset,
    form,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    hr,
    isindex,
    menu,
    noframes,
    noscript,
    ol,
    p,
    pre,
    table,
    th,
    tr,
    td,
    ul,
    li,
    dd,
    dt,
    pdftoc {
        display: block;
    }

    table {
    }

    tr,
    th,
    td {

        vertical-align: middle;
        width: auto;
    }

    th {
        text-align: center;
        font-weight: bold;
    }

    center {
        text-align: center;
    }

    big {
        font-size: 125%;
    }

    small {
        font-size: 75%;
    }


    ul {
        margin-left: 1.5em;
        list-style-type: disc;
    }

    ul ul {
        list-style-type: circle;
    }

    ul ul ul {
        list-style-type: square;
    }

    ol {
        list-style-type: decimal;
        margin-left: 1.5em;
    }

    pre {
        white-space: pre;
    }

    blockquote {
        margin-left: 1.5em;
        margin-right: 1.5em;
    }

    noscript {
        display: none;
    }
    """

    def parseHTML(data, node):
        path = None
        link_callback = None
        debug = 0
        default_css = HTML_CSS
        xhtml = False
        encoding = None
        xml_output = None
        capacity = 100 * 1024

        # Prepare simple context
        context = pisaContext(path, debug=debug, capacity=capacity)
        context.pathCallback = link_callback

        # Build story
        context = pisaStory(
            data,
            path,
            link_callback,
            debug,
            default_css,
            xhtml,
            encoding,
            context=context,
            xml_output=xml_output,
        )
        return context.story

else:  # no xhtml2pdf

    def parseHTML(data, none):
        log.error("You need xhtml2pdf installed to use the raw HTML directive.")
        return []


class DependencyRecordingFileSystemLoader(jinja2.FileSystemLoader):
    def __init__(self, *args, record_dependencies=None, **kwargs):
        self.record_dependencies = record_dependencies
        super().__init__(*args, **kwargs)

    def get_source(self, environment, template):
        r = (_, path, _) = super().get_source(environment, template)
        if self.record_dependencies is not None:
            self.record_dependencies.add(path)
        return r
