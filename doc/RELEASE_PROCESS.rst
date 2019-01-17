Release Process for rst2pdf
===========================

This is an outline of what needs to be done in order to release rst2pdf.

1. Update version number in setup.py
2. Update CHANGES.rst
3. Update version number and revision in manual
4. Build manual and upload to HTML and PDF to the website
   via a PR on the rst2pdf.github.io repo.
5. Ensure all PRs are attached to the milestone
6. Close the milestone and create next one
7. Use changelog-generator_ (or similar) to create a changelog
8. Tag release with version number
9. Update Releases section on GitHub project and paste in changelog
10. Create rc1 distribution package

    ::

       $ python setup.py egg_info -b "rc1" sdist bdist_wheel

    If you're doing an alphaX, betaX or postX, then change ``-b ""`` to ``-b "RC1"`` (or whatever)

11. Upload rc1 to Test-PyPI_

    ::

       $ twine upload --repository testpypi dist/*

    Check that it all looks correct on TestPyPI. If not, fix and release a new rc.

12. Test Test-PyPI release into a clean virtual env

    ::

       $ pip install --index-url https://test.pypi.org/simple \
         --extra-index-url https://pypi.org/simple rst2pdf

    It should install and be able to create PDF documents from rst files

13. Once rc version is working, release to PyPI_ by generating official release and uploading

    ::

       $ python setup.py egg_info -b "" sdist bdist_wheel
       $ twine upload --repository pypi dist/*



*Note:* create a ``~/.pypirc`` file to make the ``--repository`` switch work with ``twine``.
It should contain the following:

::

   [pypi]
   username: {your PyPi username}

   [testpypi]
   repository: https://test.pypi.org/legacy/
   username: {your PyPi username}



.. _changelog-generator: https://github.com/weierophinney/changelog_generator
.. _Test-PyPI: https://test.pypi.org
.. _PyPI: https://test.pypi.org




