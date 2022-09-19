Background image test
=====================

Test that we can set a background image when we initiate a page break by using the ``background`` attribute.
We can also set the fit mode using ``fit-background-mode``.

.. raw:: pdf

    PageBreak mainPage background="images/background.jpg"

This is the second page which has a background image

.. raw:: pdf

    PageBreak

This is the third page, it has no image.

.. raw:: pdf

    PageBreak background=images/background.jpg fit-background-mode=scale

This is the fourth page which has a scaled background image

.. raw:: pdf

    PageBreak

This is the fifth page, it has no image.

