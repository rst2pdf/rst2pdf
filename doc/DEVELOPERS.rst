---------------------------
Help for rst2pdf developers
---------------------------

Guidelines
~~~~~~~~~~

If you want to do something inside rst2pdf, you are welcome! The process looks something like this:

* Create an Issue for the task at https://github.com/rst2pdf/rst2pdf/issues

* If you intend to fix a bug:

  + Create a **minimal** test case that shows the bug.

  + Put it inside ``rst2pdf/tests/input`` like the others:

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

* If you added a command line option, document it in ``doc/rst2pdf.txt``.  That
  will make it appear in the manual and in the man page.

* If you implemented a new feature, please document it in ``manual.rst`` (or in
  a separate file and add an include in ``manual.rst``)

* If you implement an extension, make the docstring valid restructured text and
  link it to the manual like the others.

Git config
~~~~~~~~~~

After the mass-reformatting in PR 877, it is helpful to ignore the relevant
commits that simply reformatted the code when using git blame.

The ``..git-blame-ignore-revs`` file contains the list of commits to ignore
and you can use this git config line to make ``git blame`` work more usefully::

    git config blame.ignoreRevsFile .git-blame-ignore-revs

Pre-commit
~~~~~~~~~~

*rst2pdf* uses the `pre-commit`__ framework to automate various style checkers.
This must be enabled locally. You can install this using *pip* or your local
package manager. For example, to install using *pip*::

    pip install pre-commit

Once installed, enable it like so::

    pre-commit install --allow-missing-config

.. __: https://pre-commit.com/

If pre-commit locally behaves differently to CI, then run ``pre-commit clean`` to
clear your cache before further investigation.

Continuous Integration
~~~~~~~~~~~~~~~~~~~~~~

There's a Travis build that runs when we open a pull request or merge to master, it does some style checks and runs the test suite.

Running tests
~~~~~~~~~~~~~

The *rst2pdf* test suite generates PDFs - stored in ``rst2pdf/tests/output`` -
which are then compared against reference PDFs - stored in
``rst2pdf/tests/reference`` - using the `PyMuPDF`__ Python bindings for the
`MuPDF`__ library. *rst2pdf* depends on a number of different tools and
libraries, such as `ReportLab`__, and the output of these can vary slightly
between releases. The *PyMuPDF* library allows us to compare the structure
of the PDFs, with a minor amount of fuzzing to allow for minor differences
caused by these changes in underlying dependencies.

.. __: https://pymupdf.readthedocs.io/en/latest/
.. __: https://mupdf.com/
.. __: https://www.reportlab.com/

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


.. note::

    Some tests require the execution of the ``dot`` command, you should install
    the package graphviz from your packages manager.
