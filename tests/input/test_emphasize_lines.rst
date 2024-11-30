Highlight lines
---------------

The following code-blocks should dim all lines that are not marked with
``emphasize-lines``, and so the effect is to highlight the selected lines.

This feature is an alias of the ``hl_lines`` feature, since this option is
used by Sphinx.

With this block of plain text, lines 1 and 3 are dimmed:

.. code-block:: text
   :linenos:
   :emphasize-lines: 2

   To be
   or not to be
   that is the question

For this block of Python, lines 1, 2, 4, 6, 8, 9 and 10 are dimmed:

.. code-block:: python
   :linenos:
   :emphasize-lines: 3 5 7

   number = 0

   if number > 0:
       print("Positive number")
   elif number == 0:
       print('Zero')
   else:
       print('Negative number')

   print('This statement is always executed')

