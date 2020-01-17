---------------------------
Help for rst2pdf developers
---------------------------

Or, how do I hack this thing?

Guidelines
~~~~~~~~~~

In rst2pdf we want many things. We want ponies and icecream. But most of all,
we want rst2pdf to kick ass. The best way to achieve that is making rst2pdf
work right.  The best way to do *that* is through testing and documenting.

So, if you want to do something inside rst2pdf, you are welcome, but...

* Create an Issue for the task. That's easy, just go to
  https://github.com/rst2pdf/rst2pdf/issues and do it.

* If you intend to fix a bug:

  + Create a **minimal** test case that shows the bug.

  + Put it inside ``rst2pdf/tests/input`` like the others:

    For tests that don't involve Sphinx (e.g. reproducible with `rst2pdf`):

    - ``test_issue_NNN.txt`` is the test itself

    - ``test_issue_NNN.cli`` is any needed command line arguments (if needed)

    - ``test_issue_NNN.style`` is a custom stylesheet (if needed)

    (where ``NNN`` is the number of the issue created earlier)

    For tests that affect the Sphinx integration only, create a new Sphinx
    "project" in the ``rst2pdf/tests/input`` directory using the
    ``sphinx-quickstart`` tool. Name the directory ``sphinx-issueNNN``, where
    ``NNN``` is once again the number of the issue created earlier. Use a
    combined source and build directory and use dummy project and author names.
    Don't include ``Makefile`` or ``make.bat`` file since they won't be used.
    For example::

      sphinx-quickstart rst2pdf/tests/input/sphinx-issue123 \
        --project foo --author 'Joe Bloggs' -v 1.0.0 --language en \
        --no-makefile --no-batchfile

    Once complete, remove all unnecessary configuration from the generated
    ``conf.py`` file to allow us focus on the issue.

  + Fix the bug

    During this process, you can run the individual test case to quickly
    iterate. For example::

      pytest rst2pdf/tests/input/test_issue_NNN.txt

    You may also wish to check the logs and output::

      less rst2pdf/tests/output/test_issue_NNN.log
      xdg-open rst2pdf/tests/output/test_issue_NNN.pdf  # or 'open' on MacOS

  + Once resolved, copy the generated output PDF, if any, to
    ``rst2pdf/tests/reference`` and commit this along with the files in
    ``rst2pdf/tests/input``.

  + Submit a pull request.

* Always, when committing something, check for regressions running the full
  test suite, it takes only a minute or two. Keep in mind that regressions can
  be trivial!

  For example, if you change the spacing of definition lists, 3 or 4 tests will
  regress.

* Keep your Issues updated. If you are working on frobnozzing the gargles, then
  by all means post it in the issue. There's no issue about it? You were meant
  to create one, remember? ;-)

* If you added a command line option, document it in ``doc/rst2pdf.txt``.  That
  will make it appear in the manual and in the man page.

  Maybe it should also be available for sphinx users, let me know about it.

* If you implemented a new feature, please document it in ``manual.rst`` (or in
  a separate file and add an include in ``manual.rst``)

* If you implement an extension, make the docstring valid restructured text and
  link it to the manual like the others.

Why should you bother with all this?

It's important that you do it this way because it means that the rest of us
know what you are doing. It also means you don't break rst2pdf.


Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~

There's a Travis build - see https://github.com/rst2pdf/rst2pdf/issues/621 for
more information on the current status


Running tests
~~~~~~~~~~~~~

The *rst2pdf* test suite generates PDFs - stored in ``rst2pdf/tests/output`` -
which are then compared against reference PDFs - stored in
``rst2pdf/tests/reference`` - using the `PyMuPDF`__ Python bindings for the
`MuPDF`__ library. *rst2pdf* depends on a number of different tools and
libraries, such as `ReportLab`__ and `Inkscape`__, and the output of these can
vary slightly between releases. The *PyMuPDF* library allows us to compare the
structure of the PDFs, with a minor amount of fuzzing to allow for minor
differences caused by these changes in underlying dependencies.

.. __: https://pymupdf.readthedocs.io/en/latest/
.. __: https://mupdf.com/
.. __: https://www.reportlab.com/
.. __: https://inkscape.org/

First run
*********

To run the tests for the first time, you will need to do some setup (after
this, you can just work on your given virtualenv each time)::

    python -m venv env
    . env/bin/activate

    pip install pytest pytest-xdist
    pip install -c requirements.txt .[tests,sphinx,hyphenation,svgsupport,aafiguresupport,mathsupport,rawhtmlsupport]
    pytest

Next runs
*********

To run all tests, run::

  pytest

You can also run tests in parallel by passing the ``-n auto`` flag::

  pytest -n auto

Running a single test
*********************

To run one test only, simply pass the file or directory to pytest. For example::

  pytest rst2pdf/tests/input/sphinx-repeat-table-rows

This will run one test and show the output.

Skipping tests
**************

To skip a test, simply create a text file in the ``tests/input`` directory
called ``[test].ignore`` containing a note on why the test is skipped. This
will mark the test as skipped when the test suite runs. This could be useful
for inherited tests that we aren't confident of the correct output for, but
where we don't want to delete/lose the test entirely.


Getting commit rights
~~~~~~~~~~~~~~~~~~~~~

Just ask in the mailing list.

.. note::

    Some tests require the execution of the ``dot`` command, you should install
    the package graphviz from your packages manager.
