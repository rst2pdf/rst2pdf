plantuml images
===============

This test displays two UML diagrams created using the plantuml extension. The first one is an svg and so is left aligned.
The second is a png and as it is a raster image, it should be centre-aligned.

Note that the size of the images created by plantuml aren't exact to what is specified so we don't actually get the
size we requested. It's unknown if the size generated changes with different plantuml versions.

.. raw:: pdf

   Spacer 0 20mm


.. uml::
   :format: svg
   :width: 100
   :height: 100

   Alice -> Bob: Hi!
   Alice <- Bob: How are you?

.. uml::
   :format: png
   :width: 200
   :height: 200

   Alice -> Bob: Hi!
   Alice <- Bob: How are you?

