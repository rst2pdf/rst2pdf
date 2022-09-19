# -- General configuration -----------------------------------------------------
extensions = ['rst2pdf.pdfbuilder']
master_doc = 'index'

# -- Options for PDF output ----------------------------------------------------
# Grouping the document tree into PDF files (source start file, target file name, title, author).
pdf_documents = [('index', 'BreakLevel_2', 'Break Level Test', 'Rob Allen')]

pdf_stylesheets = ['sphinx']
pdf_use_toc = True
pdf_use_index = False
pdf_use_modindex = False
pdf_use_coverpage = False
pdf_invariant = True
pdf_breakside = 'any'

pdf_toc_depth=3
