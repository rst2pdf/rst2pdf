===========================
Release Process for rst2pdf
===========================

This is an outline of what needs to be done in order to release rst2pdf.

#. Install dependencies that you'll need
   ::

      $ pip install setuptools setuptools_scm wheel twine

#. Update ``CHANGES.rst`` to add the version number and date. Commit to a branch, PR and merge to main
#. Ensure all PRs are attached to the milestone
#. Close the milestone and create next one
#. Checkout main and ensure that your working copy is clean

   ::

      $ git checkout main

#. Use changelog-generator_ (or similar) to create a changelog

   ::

      $ changelog-generator -u rst2pdf -r rst2pdf -m 999

#. Tag release with version number

   ::

      $ git tag -s 0.94
      $ git push upstream 0.94

#. Build manual

   You will need the `White Rabbit`_ font installed. We check out the tag install via pip first so that the version
   on the first page of the PDF is labelled as final and then generate the HTML and PDF docs.

   ::

     $ git checkout 0.94
     $ pip install  -c requirements.txt -e .[aafiguresupport,mathsupport,rawhtmlsupport,sphinx,svgsupport,tests]

     $ cd doc; ./gen_docs.sh; cd ..
     $ git checkout main

   Add subject and author to manual PDF's meta data using ExifTool_

   ::

     $ exiftool -PDF:Subject="v0.94 r2019011700" doc/output/pdf/manual.pdf
     $ exiftool -PDF:Author="rst2pdf project; Roberto Alsina" doc/output/pdf/manual.pdf

   and upload to HTML and PDF to the website
   via a PR on the rst2pdf.github.io_ repo.

#. Create a new release in the Releases_ section on GitHub project

   Draft a new release, selecting the newly pushed tag and setting the Release Title to the tag name. To create the
   description, press the "Generate release notes" button and then remove the items that were by dependabot.

   Publish the release.

#. Create rc distribution package

    Double check that you do not have any changes in your working directory that are not committed. If you do, stash
    them as otherwise uploading to PyPI will not work.

    ::

       $ python setup.py egg_info -b "rc1" sdist bdist_wheel

    If you're doing an alphaX, betaX or postX, then change ``-b "rc1"`` appropriately

#. Set up PyPI if you haven't already

    Create a ``~/.pypirc`` file with sections for rst2pdf and testrstpdf which are then used with ``twine`` via the
    ``--repository`` switch.

    It should contain the following:

    ::

        [rst2pdf]
          username = __token__
          password = {your token here}

        [testrst2pdf]
          repository = https://test.pypi.org/legacy/
          username = __token__
          password = {your token here}


    You can get your token from the account settings section of https://pypi.org/ & https://test.pypi.org/


#. Upload the rc distribution to Test-PyPI_

    ::

       $ twine upload --repository testrst2pdf dist/*

    Check that it all looks correct on Test-PyPI. If not, fix and release a new rc.

#. Test Test-PyPI release into a clean virtual env

    ::

       $ pip install --index-url https://test.pypi.org/simple \
         --extra-index-url https://pypi.org/simple --pre rst2pdf

    It should install the rc release on Test PyPI and be able to create PDF documents from rst files

    Delete the build artifacts and dist files with:

    ::

        $ rm -rf build/ rst2pdf.egg-info/ dist/

#. Once rc version is working, release to PyPI_ by generating official release and uploading

    ::

       $ python setup.py egg_info -b "" sdist bdist_wheel
       $ twine upload --repository rst2pdf dist/*


    Check that the release is correct on PyPI_ and then delete the build artifacts and dist files with:

    ::

        $ rm -rf build/ rst2pdf.egg-info/ dist/

#. That's it!

    A new release of rst2pdf is now live. Celebrate by shouting about it from the rooftops!


.. _changelog-generator: https://github.com/weierophinney/changelog_generator
.. _White Rabbit:: https://squaregear.net/fonts/whitrabt.html
.. _ExifTool: https://www.sno.phy.queensu.ca/~phil/exiftool/
.. _Releases: https://github.com/rst2pdf/rst2pdf/releases
.. _rst2pdf.github.io: https://github.com/rst2pdf/rst2pdf.github.io
.. _Test-PyPI: https://test.pypi.org
.. _PyPI: https://pypi.org


Releasing as a Snap
~~~~~~~~~~~~~~~~~~~

1. Update the version string in ``snap/snapcraft.yml`` as desired (probably to match the new release tag)

2. Run ``snapcraft`` and note the filename of the output

3. Now publish (the ``rst2pdf`` namespace is associated with @lornajane's Ubuntu account) by doing ``snapcraft push --release=stable [the snape filename from the previous step]``
