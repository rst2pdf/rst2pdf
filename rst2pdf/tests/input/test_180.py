# -*- coding: utf-8 -*-
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus.paragraph import Paragraph


def go():
    styles = getSampleStyleSheet()
    style = styles['Normal']

    p1 = Paragraph('This is a paragraph', style)
    print(p1.wrap(500, 701))
    print(p1._cache['avail'])
    print(len(p1.split(500, 701)))
    print(p1.wrap(500, 700))
    print(len(p1.split(500, 700)))


go()
