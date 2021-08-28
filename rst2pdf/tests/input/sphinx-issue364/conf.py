# -*- coding: utf-8 -*-

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['rst2pdf.pdfbuilder']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'sphinx'
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
pdf_documents = [
    (
        'index',
        u'index',
        u'test1',
        u'C.G.',
        {'pdf_use_index': True, 'pdf_use_modindex': True, 'pdf_use_coverpage': True},
    ),
    (
        'index2',
        u'index2',
        u'test2',
        u'C.G.',
        {
            'pdf_use_index': False,
            'pdf_use_modindex': False,
            'pdf_use_coverpage': False,
            'pdf_compressed': True,
        },
    ),
]
pdf_stylesheets = ['sphinx', 'sphinx-issue364']
pdf_use_index = False
pdf_use_modindex = False
pdf_use_coverpage = False
pdf_invariant = True
pdf_real_footnotes = True

# Set a consistent date for the cover page
today = 'April 29, 2018'