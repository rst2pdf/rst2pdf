Intro to RST2PDF2
=================

This is my attempt to update the well-known rst2pdf utility, mainly to make
it Python 3 compatible.  The original repo (https://code.google.com/p/rst2pdf/)
hasn't seen any activity since 2012.  The primary aim of this is to get it
running under Python 3, but I am also generally tidying up the code,  
removing outdated idioms and updating it to use recent standard libraries.

After digging around in the code, it turns out that this is far from simply 
running `2to3` and updating the requirements.  Specifically, the following
issues need to be addresses:

 * Many of the dependencies are themselves outdated, and need to be either
   removed for the feature list, replaced with a new alternative, or forked 
   and updated.
 * There is little in the way of documentation, either in the code or separate
   use docs.  This makes it difficult to be certain of the full scope of
   existing functionality.
 * There are no unit tests.
 * There are functional tests, but these work by
   comparing the md5sum of generated PDFs with a known list, so are very
   dependent on the exact version of ReportLab and other packages.
 * The tests run on a large, custom testrunner which needs a lot of work
   itself.
 * The code badly needs refactoring.
 
My initial intention was to refactor, ensure that the tests pass, the update
and clean the code.  However, this is not really possible because of the lack
of reliable tests so instead I am using the following general approach 
(in order), but really just fixing issues as they arise:

#.  Get the tests working reliably with travis.  I have replaced the built 
    in testrunner with nose, and changed from comparing md5sums to performing
    a pixel-by-pixel comparison of generated PDFs.  This means that I have had
    to make several assumptions about how the generated PDFs should look, so
    it is very likely that the behaviour is already different from the original.
    It is important to note that this will only test the visual appearance
    of the PDF and not actions (such as links) or embedded data (such as author).
    Those will still need to be tested with unit tests

#.  Adding unit tests. This is a massive task to do retroactively, so I'll likely
    only add tests as I find issues which need them.

#.  The original had a few required dependencies, and several optional
    dependencies.  It used buildout for setup.  Since pip is now available,
    I have changed from buildout to using distutils (with setuptools)
    and a `requirements.txt` file.  Most of the optional dependencies will
    now be required (since pip makes them so easy to install) with the exception
    of matplotlib because of its size.

#.  Removing any code which relies on, of test for, older versions of packages.
    Specifically, this means anything that looks like, for example,

        if reportlab.version < '2.3':
            ...

    Some of this may need to be added back if there is a request to support an
    older version, but I'll leave that up to the pull request author as I have
    no inclination to add support for old versions of dependencies.
    
#.  Update all code to a consistent, PEP8 compatible style and updating python
    idioms, for example replacing

        f = open(...)
        ...
        f.close()
        
    with
    
        with open(...) as f:
            ...
            
    This includes updating deprecated stdlib functionality and adding
    docstrings everywhere.
    
#.  Add comprehensive user documentation.  Another big task to come.

PRs and issue reports are welcome!

----

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
