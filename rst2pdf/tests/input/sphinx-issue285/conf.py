# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['rst2pdf.pdfbuilder']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Issue 285'
copyright = u'2010, Roberto Alsina'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '0.0'
# The full version, including alpha/beta/rc tags.
release = '0.0'


# -- Options for PDF output ----------------------------------------------------

# Grouping the document tree into PDF files. List of tuples
# (source start file, target name, title, author).
pdf_documents = [('index', 'Issue285', u'Issue 285 Documentation', u'Roberto Alsina')]

pdf_break_level = 3
pdf_verbosity = 0
pdf_invariant = True
pdf_real_footnotes = True

# Set a consistent date for the cover page
today = 'April 29, 2018'