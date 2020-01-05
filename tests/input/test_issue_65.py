#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.platypus.tables import *
from reportlab.lib.styles import ParagraphStyle


@pytest.mark.skip(reason="ParagraphStyle complained.  Old code")
def test_go():

    Story = []
    doc = SimpleDocTemplate("phello.pdf")

    cell = [
        Paragraph(
            "A",
            ParagraphStyle(
                name="Normal", fontName="Helvetica", fontSize=10, leading=12
            ),
        ),
    ]
    # This story has only Helvetica
    # Story=cell
    # This one has helvetica and Times-Roman
    Story = cell + [Table([[cell]])]
    doc.build(Story)

