# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['rst2pdf.pdfbuilder']

# The master toctree document.
master_doc = 'contents'

# General information about the project.
project = u'issue196'
copyright = u'2009, RA'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = 'test'
# The full version, including alpha/beta/rc tags.
release = 'test'

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
show_authors = True


# -- Options for PDF output ----------------------------------------------------

# Grouping the document tree into PDF files. List of tuples
# (source start file, target name, title, author).
pdf_documents = [('contents', u'MyProject', u'My Project', u'Author Name')]

# If false, no index is generated.
pdf_use_index = False

# If false, no modindex is generated.
pdf_use_modindex = False

# If false, no coverpage is generated.
pdf_use_coverpage = False

pdf_verbosity = 0
pdf_break_level = 1
pdf_invariant = True
pdf_real_footnotes = True
