We are testing include a file using ``:include:`` with line numbers enabled using ``:linenos:``.


In the following code blocks, the line numbers always should match the numbers
in the content.

First test: ``:linenos_offset:``

.. code-block:: text
   :linenos:
   :linenos_offset:
   :include: include

Second test: ``:linenos_offset:`` & ``:start-at: Line 3``

.. code-block:: text
   :linenos:
   :include: include
   :linenos_offset:
   :start-at: Line 3

Third test: ``:linenos_offset:`` & ``start-after: Line 2``

.. code-block:: text
   :linenos:
   :include: include
   :linenos_offset:
   :start-after: Line 2

Fourth test: ``:linenos_offset:`` & ``start-after: Lin``

.. code-block:: text
   :linenos:
   :include: include
   :linenos_offset:
   :start-after: Lin

In the following, the line numbers always start at 1:

Fifth test: ``start-at: Line 3``

.. code-block:: text
   :linenos:
   :include: include
   :start-at: Line 3

Sixth test: ``start-after: Line 2``

.. code-block:: text
   :linenos:
   :include: include
   :start-after: Line 2
