===========================
Release Process for rst2pdf
===========================

This is an outline of what needs to be done in order to release rst2pdf.

#. Update ``CHANGES.rst``. Commit to a branch, PR and merge to master
#. Ensure all PRs are attached to the milestone
#. Close the milestone and create next one
#. Use changelog-generator_ (or similar) to create a changelog

   ::

      $ changelog-generator -u rst2pdf -r rst2pdf -m 999

#. Tag release with version number

   ::

      $ git tag -s 0.94
      $ git push upstream 0.94

#. Build manual

   ::

     $ cd doc; ./gen_docs.sh

   Add subject and author to manual PDF's meta data using ExifTool_

   ::

     $ exiftool -PDF:Subject="v0.94 r2019011700" output/pdf/manual.pdf
     $ exiftool -PDF:Author="rst2pdf project; Roberto Alsina" output/pdf/manual.pdf

   and upload to HTML and PDF to the website
   via a PR on the rst2pdf.github.io_ repo.

#. Update Releases section on GitHub project and paste in changelog
#. Create rc distribution package

    ::

       $ python setup.py egg_info -b "rc1" sdist bdist_wheel

    If you're doing an alphaX, betaX or postX, then change ``-b "rc1"`` appropriately

#. Upload the rc distribution to Test-PyPI_

    ::

       $ twine upload --repository testpypi dist/*

    Check that it all looks correct on Test-PyPI. If not, fix and release a new rc.

#. Test Test-PyPI release into a clean virtual env

    ::

       $ pip install --index-url https://test.pypi.org/simple \
         --extra-index-url https://pypi.org/simple rst2pdf

    It should install and be able to create PDF documents from rst files

    Delete the build artifacts and dist files with:

    ::

        $ rm -rf build/ rst2pdf.egg-info/ dist/

#. Once rc version is working, release to PyPI_ by generating official release and uploading

    ::

       $ python setup.py egg_info -b "" sdist bdist_wheel
       $ twine upload --repository pypi dist/*


    Check that the release is correct on PyPI_ and then delete the build artifacts and dist files with:

    ::

        $ rm -rf build/ rst2pdf.egg-info/ dist/

|
|

*Note:* create a ``~/.pypirc`` file to make the ``--repository`` switch work with ``twine``.
It should contain the following:

::

   [pypi]
   username: {your PyPi username}

   [testpypi]
   repository: https://test.pypi.org/legacy/
   username: {your PyPi username}


.. _ExifTool: https://www.sno.phy.queensu.ca/~phil/exiftool/
.. _rst2pdf.github.io: https://github.com/rst2pdf/rst2pdf.github.io
.. _changelog-generator: https://github.com/weierophinney/changelog_generator
.. _Test-PyPI: https://test.pypi.org
.. _PyPI: https://test.pypi.org


Releasing as a Snap
~~~~~~~~~~~~~~~~~~~

1. Update the version string in ``snap/snapcraft.yml`` as desired (probably to match the new release tag)

2. Run ``snapcraft`` and note the filename of the output

3. Now publish (the ``rst2pdf`` namespace is associated with @lornajane's Ubuntu account) by doing ``snapcraft push --release=stable [the snape filename from the previous step]``
