Intro
=====

The usual way of creating PDF from reStructuredText is by going through LaTeX.
This tool provides an alternative by producing PDF directly using the ReportLab
library.

More information is available `at the main website`__

__ http://rst2pdf.ralsina.me/stories/index.html

Features
========

* User-defined page layout. Multiple frames per page, multiple layouts per
  document.

* Page transitions

* Cascading stylesheet mechanism, define only what you want changed.

* Supports TTF and Type1 font embedding.

* Any number of paragraph styles using the class directive.

* Any number of character styles using text roles.

* Custom page sizes and margins.

* Syntax highlighter for many languages, using Pygments.

* Supports embedding almost any kind of raster or vector images.

* Supports hyphenation and kerning (using wordaxe).

* `Full user's manual`__

__ http://ralsina.me/static/manual.pdf

Installation and use
====================

Install from PyPI
-----------------

The latest released version, 0.93, may be installed from PyPI by using
pip or easy_install.  It does not support Python 3::

  sudo pip install rst2pdf

Install from github
--------------------

Work on rst2pdf has restarted on github, with the goals of supporting
Python 3, addressing outstanding issues, and not breaking anything. You
can clone the repository and install this version::

  git clone https://github.com/rst2pdf/rst2pdf my_clone_name
  cd my_clone_name
  git checkout <desired-branch> # if you want something other than master
  sudo python setup.py install

You may want to install it in a virtualenv, but that is beyond the scope
of this readme.

Quick-start
------------

To convert a restructuredText document to a PDF, simply::

  rst2pdf <document name> output.pdf
