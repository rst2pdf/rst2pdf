#!/usr/bin/env python
# -*- coding: utf-8 -*-

from copy import copy

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate
from reportlab.platypus.xpreformatted import XPreformatted


def go():
    Story = []
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate("issue216.pdf")

    knstyle = copy(styles['Normal'])
    heading = Paragraph('A heading at the beginning of the document', knstyle)
    heading.keepWithNext = True
    content = XPreformatted('This is the content\n' * 120, styles['Normal'])

    Story = [heading, content]
    doc.build(Story)


go()
