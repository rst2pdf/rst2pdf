# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['rst2pdf.pdfbuilder']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'sample'
copyright = u'2010, sample'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
release = '1.0'


# -- Options for PDF output ----------------------------------------------------

# Grouping the document tree into PDF files. List of tuples
# (source start file, target name, title, author).
pdf_documents = [('index', u'sample', u'sample Documentation', u'sample')]
pdf_stylesheets = ['sphinx', 'a4', 'ja']

pdf_font_path = ['../..']

pdf_invariant = True
pdf_real_footnotes = True

# Set a consistent date for the cover page
today = 'April 29, 2018'