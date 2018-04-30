===========================
Help for rst2pdf developers
===========================

-----------------------------
Or, how do I hack this thing?
-----------------------------

Guidelines
----------

In rst2pdf we want many things. We want ponies and icecream. But most of all, we want
rst2pdf to kick ass. The best way to achieve that is making rst2pdf work right.
The best way to do *that* is through testing and documenting.

So, if you want to do something inside rst2pdf, you are welcome, but...

* Create an Issue for the task. That's easy, just go to
  https://github.com/rst2pdf/rst2pdf/issues and do it.

* If you intend to fix a bug:

  + Create a **minimal** test case that shows the bug.

  + Put it inside ``rst2pdf/tests/input`` like the others:

    - ``mytest.txt`` is the test itself

    - ``mytest.cli`` is any needed command line arguments (if needed)

    - ``mytest.style`` is a custom stylesheet (if needed)

  + Run the test suite on it::

      cd rst2pdf/tests
      ./autotest.py input/mytest.txt

  + Check the output::

      less output/mytest.log
      acroread output/mytest.pdf

  + If it's really a bug, mark the test as *bad* and save everything in git::

      setmd5 bad input/mytest.txt
      git checkout -b issue-X
      git add input/mytest.*
      git add md5/mytest.json
      git commit -m "Test case for Issue X"
      git push -u origin issue-X # then open a Pull Request

* Always, when committing something, check for regressions running the full test suite,
  it takes only a minute or two. Keep in mind that regressions can be trivial!

  For example, if you change the spacing of definition lists, 3 or 4 tests will
  regress.

* Keep your Issues updated. If you are working on frobnozzing the gargles, then by
  all means post it in the issue. There's no issue about it? You were meant to
  create one, remember? ;-)

* If you added a command line option, document it in ``doc/rst2pdf.txt``.
  That will make it appear in the manual and in the man page.

  Maybe it should also be available for sphinx users, let me know about it.

* If you implemented a new feature, please document it in ``manual.rst``
  (or in a separate file and add an include in ``manual.rst``)

* If you implement an extension, make the docstring valid restructured text
  and link it to the manual like the others.

Why should you bother with all this?

It's important that you do it this way because it means that the rest of us know what you are doing. It also means you don't break rst2pdf.

Continuous Integration
----------------------

There's a Travis build - see https://github.com/rst2pdf/rst2pdf/issues/621 for more information on the current status

Running tests
-------------

The rst2pdf test suite generates PDFs, then calculates a checksum (an md5) of the resulting file and checks it against known lists of good and bad md5s. These known outcomes are in ``rst2pdf/tests/md5/[test_name].json`` (warning, not actually a json file).

First run
~~~~~~~~~

To run the tests for the first time, you will need to do some setup (after this, you can just work on your given virtualenv each time).

::

    virtualenv --python=/usr/local/bin/python2 env
    . env/bin/activate

    pip install nose coverage
    pip install -r requirements.txt
    pip install -e .[tests,sphinx,images,svgsupport,aafiguresupport,mathsupport,rawhtmlsupport]
    nosetests -v -i regulartest -i sphinxtest

Next runs
~~~~~~~~~

While in project::

  nosetests -v -i regulartest -i sphinxtest


To stop the tests on the first failure, use the ``-x`` switch::

  nosetests -x -i regulartest -i sphinxtest


Using autotest directly
~~~~~~~~~~~~~~~~~~~~~~~

You can also run the tests using autorun directly::

  cd rst2pdf/tests
  ./autotest.py -e -f >& /dev/null
  ./parselogs.py > log.txt


Now look at the output of ``log.txt``

Running a single test
~~~~~~~~~~~~~~~~~~~~~

To run one test only, try this::

  cd rst2pdf/tests
  ./autotest.py input/[test].txt

This will run one test and show the output.

Skipping tests
~~~~~~~~~~~~~~

To skip a test, simply create a text file in the ``tests/input`` directory called ``[test].ignore`` containing a note on why the test is skipped. This will mark the test as skipped when the test suite runs. This could be useful for inherited tests that we aren't confident of the correct output for, but where we don't want to delete/lose the test entirely.

Marking a failing test as good
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes the local combination of software versions will create the "right" PDF but the binary file will have some minor differences. If your file looks good, then you can store the checksum of it as a valid outcome with a command like this::

  cd rst2pdf/tests
  ./autotest.py -u good input/[test].txt

You'll see from ``git diff`` that you now have a new entry in the related ``md5/[test].json`` file. Commit this to a new branch and open a pull request explaining what you did.

Getting commit rights
---------------------

Just ask in the mailing list.
