Testing rst2pdf math support and then bringing it to the level of sphinx's math extension.

Inline Math
~~~~~~~~~~~

Since Pythagoras, we know that :math:`a^2 + b^2 = c^2`.

Math Directive
~~~~~~~~~~~~~~

A single formuala using the math directive:

.. math::

   \frac{2 \pm \sqrt{7}}{3}


Simple math can go as argument of the directive

.. math:: (a + b)^2 = a^2 + 2ab + b^2


The :eq:`euler` label should point at this equation:

.. math:: e^{i\pi} + 1 = 0
   :label: euler



Non-working examples
--------------------

This below should go in two lines:

.. math::

   (a + b)^2 = a^2 + 2ab + b^2

   (a - b)^2 = a^2 - 2ab + b^2

Aligned equations:
   
.. math::
    
   (a + b)^2  &=  (a + b)(a + b) \\
              &=  a^2 + 2ab + b^2

Using ``:nowrap:`` doesn't work:

.. math::
   :nowrap:

   \begin{eqnarray}
      y    & = & ax^2 + bx + c \\
      f(x) & = & x^2 + 2xy + y^2
   \end{eqnarray}
