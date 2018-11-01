#!/bin/sh

rst2pdf manual.rst -o manual.pdf -s manual.style -b1
rst2man rst2pdf.rst rst2pdf.1
python rst2html-manual.py --stylesheet=manual.css manual.rst manual.html
