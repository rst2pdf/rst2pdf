# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2012 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

__version__ = '0.1'

from .pdfwriter import PdfWriter
from .pdfreader import PdfReader
from .objects import PdfObject, PdfName, PdfArray, PdfDict, IndirectPdfDict, PdfString
from .tokens import PdfTokens
from .errors import PdfParseError

# Add a tiny bit of compatibility to pyPdf

PdfFileReader = PdfReader
PdfFileWriter = PdfWriter
