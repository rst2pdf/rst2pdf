Testing the ``linenos`` option for code blocks
==============================================

This is a code block without ``:linenos:``. The line numbers should not display.

.. code-block:: python

    "line 1 without linenos"
    "line 2"

    "line 4"





    "line 10"


This is a code block with ``:linenos:`` is set with no value. The line numbers should display.

.. code-block:: python
    :linenos:

    "line 1 with linenos="
    "line 2"

    "line 4"





    "line 10"

.. raw:: pdf

  PageBreak


Boolean values
--------------

This is a code block with ``:linenos:`` is set to ``true`` (lowercase). The line numbers should display.

.. code-block:: python
    :linenos: true

    "line 1 with linenos=true"
    "line 2"

    "line 4"





    "line 10"

This is a code block with ``:linenos:`` is set to ``True`` (capitalized). The line numbers should display.

.. code-block:: python
    :linenos: True

    "line 1 with linenos=True"
    "line 2"

    "line 4"





    "line 10"


This is a code block with ``:linenos:`` is set to ``false`` (lowercase). The line numbers should not display.

.. code-block:: python
    :linenos: false

    "line 1 with linenos=false"
    "line 2"

    "line 4"





    "line 10"


This is a code block with ``:linenos:`` is set to ``False`` (capitalized). The line numbers should not display.

.. code-block:: python
    :linenos: False

    "line 1 with linenos=False"
    "line 2"

    "line 4"





    "line 10"
