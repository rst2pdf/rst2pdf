# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.todo', 'rst2pdf.pdfbuilder']

# The suffix of source filenames.
source_suffix = '.rst'

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


# -- Options for sphinx.ext.todo extension -----------------------------------

todo_include_todos = True


# -- Options for PDF output --------------------------------------------------

# Grouping the document tree into PDF files. List of tuples
# (source start file, target name, title, author, options).
pdf_documents = [
    ('index', u'index', u'index', u'lorenzo'),
]

# A comma-separated list of custom stylesheets. Example:
pdf_stylesheets = ['sphinx']

# Language to be used for hyphenation support
pdf_language = "en_US"

# If false, no index is generated.
pdf_use_index = False

# If false, no coverpage is generated.
pdf_use_coverpage = False

pdf_invariant = True
