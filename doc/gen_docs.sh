#!/bin/sh

rst2pdf manual.rst --custom-cover=assets/cover.tmpl -o output/pdf/manual.pdf -s assets/manual.yaml -b1

# Determine correct name for rst2man
RST2MAN="rst2man"
if [ -x "$(command -v rst2man.py)" ]; then
    RST2MAN="rst2man.py"
fi
$RST2MAN rst2pdf.rst output/rst2pdf.1

# set PYTHONPATH so we use the current contents of this repo, rather than our installed rst2pdf
PYTHONPATH=../ python rst2html-manual.py --stylesheet=assets/manual.css manual.rst output/html/manual.html
cp assets/biohazard.png output/html/assets/
