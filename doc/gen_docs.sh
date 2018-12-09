#!/bin/sh

rst2pdf manual.rst --custom-cover=assets/cover.tmpl -o output/manual.pdf -s assets/manual.style -b1
rst2man rst2pdf.rst output/rst2pdf.1

# set PYTHONPATH so we use the current contents of this repo, rather than our installed rst2pdf
PYTHONPATH=../ python rst2html-manual.py --stylesheet=assets/manual.css manual.rst output/manual.html
