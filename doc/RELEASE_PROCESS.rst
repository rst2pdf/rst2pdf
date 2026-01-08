===========================
Release Process for rst2pdf
===========================

This is an outline of what needs to be done in order to release rst2pdf.

#. Install ``uv``, please see `the installation docs <https://docs.astral.sh/uv/getting-started/installation/>`_
#. You will also need the need the `White Rabbit`_ font installed in order to create the manual

#. Update ``CHANGES.rst`` to add the version number and date
#. Run ``uv lock`` to update the ``uv.lock`` file
#. Commit to a branch, PR and merge to main

#. Ensure all PRs are attached to the milestone
#. Close the milestone and create next one

#. On the Releases page, click "Draft a new release"
#. Go to "Choose a tag" and type the new tag name (e.g., 0.103) to create on publish, target the main branch
#. Click "Generate release notes" and edit the resulting output
#. Now publish the new release

#. Build manual

   Check out the tag first and then install via ``uv``. We do this so that the version number that
   is rendered to the first page of the PDF is displayed as "{version number} (final)" rather than
   as a dev version.

   ::

     $ git checkout 0.103
     $ uv sync --all-extras

   Generate the HTML and PDF docs:

   ::

     $ cd doc; ./gen_docs.sh; cd ..
     $ git checkout main

   Add subject (version info plus r, datetime, and revision number) and author to manual PDF's meta data using ExifTool_ e.g.

   ::

     $ exiftool -PDF:Subject="v0.104 r2026010800" doc/output/pdf/manual.pdf
     $ exiftool -PDF:Author="rst2pdf project; Roberto Alsina" doc/output/pdf/manual.pdf

   and upload to HTML and PDF to the website
   via a PR on the rst2pdf.github.io_ repo.

#. Create rc distribution package

    Double check that you do not have any changes in your working directory that are not committed. If you do, stash
    them as otherwise uploading to PyPI will not work.

    Note this step uses a workaround as per https://github.com/pypa/setuptools/issues/4129 as ``build`` and
    ``setuptools`` don't have full support for appending arbitrary tags to version numbers at build time.

    ::

       $ echo -e "[egg_info]\ntag_build=rc1\n" > /tmp/build_opts.cfg
       $ DIST_EXTRA_CONFIG=/tmp/build_opts.cfg uv build
       $ rm /tmp/build_opts.cfg

    If you're doing an alphaX, betaX or postX, then change ``tag_build=rc1`` appropriately

#. Upload the rc distribution to Test-PyPI_. You can get your token from the account settings section of
   https://test.pypi.org/.

    ::

       $ uv publish --publish-url https://test.pypi.org/legacy/ --token {your token here}

    Check that it all looks correct on Test-PyPI. If not, fix and release a new rc.

#. Test Test-PyPI release into a clean virtual env in your project root
   (specify the correct version number below). It should install the rc release
   on Test PyPI and be able to create PDF documents from rst files e.g.

    ::

       $ uvx -n --index-url https://test.pypi.org/simple --extra-index-url https://pypi.org/simple --prerelease allow \
         --index-strategy unsafe-best-match rst2pdf@0.104rc1 tests/input/test_tableofcontents.rst

   Look in the ``tests/input/`` directory and check that the ``test_tableofcontents.pdf`` file was created.

#. Delete the build artifacts and dist files with:

    ::

       $ rm -rf build/ rst2pdf.egg-info/ dist/

#. Once rc version is working, release to PyPI_ by generating building the release and publishing. You can get your
   token from the account settings section of https://pypi.org/.

    ::

       $ uv build --no-sources
       $ uv publish --token {your token here}

    Check that the release is correct on PyPI_ and then delete the build artifacts and dist files with:

    ::

       $ rm -rf build/ rst2pdf.egg-info/ dist/

#. That's it!

    A new release of rst2pdf is now live. Celebrate by shouting about it from the rooftops!


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

3. Now publish (the ``rst2pdf`` namespace is associated with @lornajane's Ubuntu account) by doing ``snapcraft push --release=stable [the snap filename from the previous step]``
