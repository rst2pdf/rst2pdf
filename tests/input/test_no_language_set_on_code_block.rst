No language
===========

This test checks that the language attribute of a code-block does not cause an error when it is not supplied.

To pass, there should be no errors on the command line and the code block below should be styled as plain text.

.. code-block::

    This is a code block with no language specified as the language is optional
    as per https://docutils.sourceforge.io/docs/ref/rst/directives.html#code
