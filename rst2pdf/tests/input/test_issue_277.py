#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import copy

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus.tables import Table, TableStyle


def go():
    Story = []
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate("issue277.pdf")
    ts = TableStyle()
    knstyle = copy(styles['Normal'])
    heading = Paragraph('A heading at the beginning of the document', knstyle)
    heading.keepWithNext = True
    print([['This is the content'] for x in range(12)])
    content = Table(
        [[Paragraph('This is the content', styles['Normal'])] for x in range(120)],
        style=ts,
    )

    Story = [heading, content]
    doc.build(Story)


go()
