# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'rst2pdf.pdfbuilder']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Test Case'
copyright = u'2009, vorsorge'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1'
# The full version, including alpha/beta/rc tags.
release = '1'

# -- Options for PDF output ----------------------------------------------------

# Grouping the document tree into PDF files. List of tuples
# (source start file, target name, title, author, options).
pdf_documents = [('index', 'TestCase', u'A Sphinx Test Case', u'vorsorge')]

# A comma-separated list of custom stylesheets. Example:
pdf_stylesheets = ['sphinx', 'letter']

# Section level that forces a break page.
# For example: 1 means top-level sections start in a new page
# 0 means disabled
pdf_break_level = 1

# verbosity level. 0 1 or 2
pdf_verbosity = 2

# If false, no coverpage is generated.
pdf_use_coverpage = True

pdf_invariant = True
pdf_real_footnotes = True

# Set a consistent date for the cover page
today = 'April 29, 2018'