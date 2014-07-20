Intro to RST2PDF2
=================

This is attempt to update the well-known rst2pdf utility, mainly to make
it Python 3 compatible.  The original repo (https://code.google.com/p/rst2pdf/)
hasn't seen any activity since 2012.  The primary aim of this is to get it
running under Python 3, but I am also generally tidying up the code,  
removing outdated idioms and updating it to use recent standard libraries.
The current status is that a lot of tests are failing, but it appears that
most of them relate to the same issues, so much of it should run fine under
Python 3.4.  The main items on the todo list are:

* Replace the packaged test runner written for rst2pdf with nose to reduce
  the maintenance burden.
  
* Fix the remaining failing tests.

* Add CI testing via TravisCI.

* Use six to make the code compatible with Python 2.7.

My focus is getting it running enough to do what I need, so any pull requests
would be appreciated!

What follows is the original readme.

Intro
=====

The usual way of creating PDF from reStructuredText is by going through LaTeX. 
This tool provides an alternative by producing PDF directly using the ReportLab
library. 

Installing
==========

python setup.py install

should do the trick.

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

* Full user's manual
