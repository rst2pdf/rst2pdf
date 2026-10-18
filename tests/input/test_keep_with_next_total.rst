.. footer:: Page ###Page### of ###Total###

Keep with next across multiple builds
======================================

Setting ``###Total###`` in the footer causes a second build pass which caused
headings to lose their ``keepWithNext`` setting, resulting in headings
stranded at the bottom of a page.

This test passes if the PDF has two pages and the "Second section" title
is at the top of page 2 and not at the bottom of page 1.

.. raw:: pdf

   Spacer 0 19.5cm


This should be the last line of page 1.


Second section
==============

This paragraph forces the "Second section" title to render on page two.
