# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['rst2pdf.pdfbuilder']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'issue162'
copyright = u'2009, RA'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = 'test'
# The full version, including alpha/beta/rc tags.
release = 'test'


# -- Options for PDF output ----------------------------------------------------

# Grouping the document tree into PDF files. List of tuples
# (source start file, target name, title, author).
pdf_documents = [('index', u'MyProject', u'My Project', u'Author Name')]

# A comma-separated list of custom stylesheets. Example:
pdf_stylesheets = ['buggy']

# A colon-separated list of folders to search for fonts. Example:
# pdf_font_path=['/usr/share/fonts', '/usr/share/texmf-dist/fonts/']
pdf_font_path = ['../']

# If false, no index is generated.
pdf_use_index = False

# If false, no modindex is generated.
pdf_use_modindex = False

# If false, no coverpage is generated.
pdf_use_coverpage = False

pdf_verbosity = 0
pdf_invariant = True
pdf_real_footnotes = True
