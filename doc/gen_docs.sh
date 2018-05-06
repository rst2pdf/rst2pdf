#!/bin/sh

rst2pdf manual.rst -o manual.pdf -s manual.style -b1
rst2man rst2pdf.rst rst2pdf.1
