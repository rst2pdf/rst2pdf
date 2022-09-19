# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.todo',
    'sphinx.ext.imgmath',
    'sphinx.ext.graphviz',
    'rst2pdf.pdfbuilder',
]

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Foobar'
copyright = u'2009, Jason S'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.0.1'
# The full version, including alpha/beta/rc tags.
release = '1.0.1'


# -- Options for PDF output ----------------------------------------------------

# Grouping the document tree into PDF files. List of tuples
# (source start file, target name, title, author, options).
pdf_documents = [('index', u'index', u'index', u'lorenzo')]

# Language to be used for hyphenation support
pdf_language = "en_US"

# verbosity level. 0 1 or 2
pdf_verbosity = 0

pdf_invariant = True
pdf_real_footnotes = True

# Set a consistent date for the cover page
today = 'April 29, 2018'