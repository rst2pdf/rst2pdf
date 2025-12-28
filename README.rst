.. image:: https://img.shields.io/pypi/v/rst2pdf.svg
    :target: https://pypi.org/project/rst2pdf/

.. image:: https://img.shields.io/pypi/pyversions/rst2pdf.svg
    :target: https://pypi.org/project/rst2pdf/

.. image:: https://img.shields.io/pypi/l/rst2pdf.svg
    :target: https://pypi.org/project/rst2pdf/

=======================================
rst2pdf: Use a text editor. Make a PDF.
=======================================

The usual way of creating PDF from reStructuredText is by going through LaTeX.
This tool provides an alternative by producing PDF directly using the ReportLab
library.

More information is available at the `main website <https://rst2pdf.org>`_.


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

* Supports hyphenation.

* `Sphinx <https://www.sphinx-doc.org>`_ integration

* `Full user's manual <https://rst2pdf.org/manual.html>`_

Installation
------------

*rst2pdf* supports Python 3.10 or greater. Version 0.103 was the last version
to support Python 3.9 Version 0.102 was the last version to support Python 3.8.

Install from PyPI (pipx)
~~~~~~~~~~~~~~~~~~~~~~~~

The latest released version may be installed from PyPI by using ``pipx``::

    $ pipx install rst2pdf

rst2pdf also has support for a number of features that require additional dependencies. Installation of all the
required dependencies using ``pipx`` may be installed using::

    $ pipx install rst2pdf[aafiguresupport,mathsupport,plantumlsupport,rawhtmlsupport,sphinx,svgsupport]

Install from PyPI (uv)
~~~~~~~~~~~~~~~~~~~~~~

As with ``pipx`` above, the latest released version may be installed from PyPI by using
`uv <https://docs.astral.sh/uv>`_::

    $ uv tool install rst2pdf

If you don't have ``uv``, please see `the installation docs <https://docs.astral.sh/uv/getting-started/installation/>`_

Installation of all the required dependencies using ``uv`` may be installed using::

    $ uv tool install rst2pdf[aafiguresupport,mathsupport,plantumlsupport,rawhtmlsupport,sphinx,svgsupport]

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
    $ git checkout <desired-branch> # if you want something other than main
    $ uv tool install .[aafiguresupport,mathsupport,plantumlsupport,rawhtmlsupport,sphinx,svgsupport]

If you intend to work on rst2pdf's source code, see ``doc/DEVELOPERS.rst``.

Usage
-----

To convert a reStructuredText document to a PDF, simply run::

    $ rst2pdf <document name> output.pdf

For information on available options, use ``-h``::

    $ rst2pdf -h

To enable basic integration with Sphinx, modify your ``conf.py`` file to enable
the ``rst2pdf.pdfbuilder`` extension and configure the ``pdf_documents``
option. For example::

    extensions = [
        # ...
        'rst2pdf.pdfbuilder',
    ]

    # Grouping the document tree into PDF files. List of tuples
    # (source start file, target name, title, author, options).
    pdf_documents = [
        ('index', 'MyProject', 'My Project', 'Author Name'),
    ]

For information on the ``pdf_documents`` option and the many other options
available, refer to the `manual <https://rst2pdf.org/static/manual.pdf>`_.

Contributing
------------

See `CONTRIBUTING <CONTRIBUTING.rst>`_.

Code of conduct
---------------

rst2pdf is an inclusive and welcoming community. To participate in this project, everyone is bound by our
`Community Code of Conduct <CODE_OF_CONDUCT.rst>`_.
