#!/bin/sh

python ../rst2pdf/createpdf.py manual.txt -o manual.pdf -s manual.style -b1
rst2man rst2pdf.txt rst2pdf.1
