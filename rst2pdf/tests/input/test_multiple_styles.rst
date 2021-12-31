Multiple styles test
====================

This test ensures that multiple classes can be applied to an element and that order matters.

Class definitions:

.. code-block:: yaml
   :include: test_multiple_styles.yaml

|

``.. class:: foo``:

.. class:: foo

This is red, left aligned and large.

|

``.. class:: bar``:

.. class:: bar

This is blue, centre aligned and small.

|

``.. class:: foo bar``:

.. class:: foo bar

This is blue, centre aligned and large.

|

``.. class:: bar foo``:

.. class:: bar foo

This is red, centre aligned (as ``foo`` doesn't specify aligment)  and large.
