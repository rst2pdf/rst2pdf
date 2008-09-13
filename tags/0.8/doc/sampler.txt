The rst2pdf Sampler
===================

--------------------
Or, what does it do?
--------------------

.. footer:: Page ###Page###

.. header:: ###Title###


.. raw:: pdf

   PageBreak twoColumn

This document tries to show you some of the nifty things rst2pdf can do. Each one of these should be
explained in The Friendly Manual :sup:`TM` For example, you are now
reading this in a two-column layout. However, the previous page had a one-column layout.

That's because rst2pdf lets you change the page layout as many times as you want, and define
layouts almost arbitrarily complex (as long as you like rectangular frames full of text, that is).

Did you notice there is a hyphen in the previous paragraph? And that it's aligned *justified*? 

On the top and bottom of this page (but not of the previous one), you can see a header and a footer 
showing you the current page and document name. They could also show a section name and number, but
this document is too short for that.

Let's go back to one-column now, but first some filler, so you can see the pretty columns.

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Suspendisse pede. Nam auctor. Donec ac urna. Quisque tempus, dui sit amet cursus euismod, leo arcu ullamcorper ligula, a elementum elit augue eu ipsum. Donec sem. Aliquam adipiscing nunc ut ante. Praesent consectetuer lacinia nulla. Pellentesque ut augue nec ante gravida vestibulum. Nunc dignissim odio ut elit. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Suspendisse malesuada porta sapien. Suspendisse congue. Morbi eget nulla at purus auctor molestie. Nulla nec orci. Duis condimentum luctus sem. Etiam elementum, turpis non blandit molestie, magna felis faucibus risus, eu ultrices risus lacus at ante. Nullam sed dui nec eros iaculis facilisis.

Morbi massa. Pellentesque metus sem, tincidunt at, hendrerit et, faucibus nec, arcu. Aenean non arcu. Sed enim odio, adipiscing at, pretium ac, porttitor ac, enim. Vestibulum sollicitudin porttitor leo. Quisque ut augue sed magna sagittis aliquam. Vestibulum lobortis. Aenean at sem a risus molestie cursus. Fusce commodo pharetra orci. Pellentesque eleifend. Sed suscipit, erat sed vestibulum feugiat, eros purus pretium quam, ut molestie pede odio sit amet ipsum. Sed eu pede. Phasellus molestie. Cras nec nulla et diam lacinia viverra. Duis libero. Aliquam tempor ligula quis leo.

Nullam ac sem. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Suspendisse potenti. Nunc a libero vitae enim cursus elementum. Nullam sit amet pede eget sapien mattis dapibus. Suspendisse nec mi eu elit pharetra ultricies. Proin mollis mattis metus. Duis viverra, tortor in suscipit imperdiet, lorem sapien dapibus mi, vehicula ultricies dolor dolor ut libero. Sed dapibus, arcu vitae eleifend pharetra, nulla nibh dignissim quam, vitae lacinia leo ipsum ut turpis. Nulla justo justo, pretium blandit, mollis ac, accumsan ac, massa. Quisque lacinia quam. Cras molestie elit eu lorem. Donec vitae lorem. Vivamus iaculis, ante ullamcorper dignissim posuere, tortor sem vestibulum nunc, vel pulvinar nisl quam sit amet erat. Cras pulvinar neque eu mi. Maecenas hendrerit dapibus elit.

.. raw:: pdf

   PageBreak oneColumn

One of the things I am pretty proud of in rst2pdf is our sidebars. ReST has a sidebar directive that 
lets you go "outside the flow of text" for the document. Like this:
  
.. sidebar:: Outside the flow

   This sidebar is outside the flow of the text.
   
And now we are back in the boring old text flow. You can make arbitrary fragments of code go "float" using the 
sidebar *class*, too. This doesn't yet work for code block, but it does work for anything else.
There is a bug about starting a sidebar while we are *besides* a sidebar, so I will jump to the next page now.

.. raw:: pdf

   PageBreak

.. class:: sidebar

This is **not** a sidebar. Really. It just looks like one. If it were a sidebar it would have a title!

And back to the old text flow.

Of course, since the authors are programmers, we want our code to look pretty:

.. code-block:: python

   print ("Hello world")

.. class:: palatino

You can also embed fonts easily. This paragraph is in font Palatino, which is not a standard PDF font. Or rather Palladio, because Palatino costs money. True Type and Type1 fonts are supported. There are **thousands** of free fonts.

.. role:: redpalatino

You can even switch fonts and colors :redpalatino:`in the middle` of the text.
  
More things will be added to this sampler as time allows it.

