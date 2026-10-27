# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

extensions = ['rst2pdf.pdfbuilder']
master_doc = 'index'
project = u'issue1318'
copyright = u'2026, RA'
version = 'test'
release = 'test'

# -- Options for PDF output ----------------------------------------------------

pdf_documents = [('index', u'MyProject', u'My Project', u'Author Name')]
pdf_stylesheets = ['sphinx']
pdf_language = "en_US"
pdf_use_index = False
pdf_use_modindex = False
pdf_use_coverpage = False
pdf_verbosity = 0
pdf_invariant = True
