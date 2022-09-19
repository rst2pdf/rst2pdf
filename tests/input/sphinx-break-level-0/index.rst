rst2pdf Sphinx pdf_break_level test
###################################

This test looks at what the pdf_break_level option does.

* ``pdf_break_level = 0``: Everything is on a single page.
* ``pdf_break_level = 1``: A new page after each section, but not sub-section
* ``pdf_break_level = 2``: A new page after each section, *and* sub-section

To generate locally, run ``sphinx-build -b pdf . ./pdf``

The next section
################

This is the next section of the document. This will be on a new page if ``pdf_break_level >= 1``.

The first sub-section
=====================

This is the first sub-section of the *next section*. This will be on a new page if ``pdf_break_level >= 2``.

The second sub-section
======================

This is the second sub-section of the *next section*. This will be on a new page if ``pdf_break_level >= 2``.

The section after next
######################

This is the section after next of the document. This will be on a new page if ``pdf_break_level >= 1``.

Another first sub-section
=========================

This is the first sub-section of the *section after next*. This will be on a new page if ``pdf_break_level >= 2``.

Another second sub-section
==========================

This is the second sub-section of the *section after next*. This will be on a new page if ``pdf_break_level >= 2``.
