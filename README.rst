.. image:: https://travis-ci.org/rst2pdf/rst2pdf.svg?branch=master
    :target: https://travis-ci.org/rst2pdf/rst2pdf

.. image:: https://img.shields.io/pypi/v/rst2pdf.svg
    :target: https://pypi.org/project/rst2pdf/

.. image:: https://img.shields.io/pypi/pyversions/rst2pdf.svg
    :target: https://pypi.org/project/rst2pdf/

.. image:: https://img.shields.io/pypi/l/rst2pdf.svg
    :target: https://pypi.org/project/rst2pdf/


========================================
rst2pdf: Use a text editor. Make a PDF.
========================================

The usual way of creating PDF from reStructuredText is by going through LaTeX.
This tool provides an alternative by producing PDF directly using the ReportLab
library.

More information is available `at the main website`__

__ https://rst2pdf.org


Features
--------

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

__ https://rst2pdf.org/static/manual.pdf


Installation
------------

*rst2pdf* supports Python 3.6 or greater. Version 0.97 was the last version to support Python 2.7.

Install from PyPI
~~~~~~~~~~~~~~~~~

The latest released version may be installed from PyPI by using
``pip``.

    $ pip3 install --user rst2pdf

Install from Snap
~~~~~~~~~~~~~~~~~

If you are using a system that supports `snaps <https://snapcraft.io/>`__
then you can install from there with::

    $ snap install rst2pdf

Install from GitHub
~~~~~~~~~~~~~~~~~~~

Work on rst2pdf has restarted on GitHub, with the goals of adding new
features, addressing outstanding issues, and not breaking anything. You
can clone the repository and install this version::

    $ git clone https://github.com/rst2pdf/rst2pdf
    $ cd rst2pdf
    $ git checkout <desired-branch> # if you want something other than master
    $ pip3 install --user .

You may want to install it in a virtualenv, but that is beyond the scope
of this readme.


Usage
-----

To convert a restructuredText document to a PDF, simply run::

    $ rst2pdf <document name> output.pdf


Contributing
------------

rst2pdf wishes to be a welcoming community. With that in mind, please refer to our `CODE_OF_CONDUCT`__.

__ CODE_OF_CONDUCT.rst
