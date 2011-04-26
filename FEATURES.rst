Countdowns
----------

Create a new ``oscar.merchandising`` app and add a feature (similar to promos) for having 
product countdowns.  This is so a client can create a new page using the ``django.contrib.flatpages``
app and add a product countdown to it.

* A countdown is defined by a title, the page URL it is found on, a description and a list of ordered products
* A countdown can be added to any page
* A context processor is needed to add the bindings to the page
* A template tag is needed to render any page "merchandising" within the page - this should be in the generic
  flatpages template


Merchandising blocks
--------------------

Similar to countdowns.  These should allow an admin to add any numbers of "blocks" to a single page
and control the order of them.

* A block is defined by a list of products together with a title, a description, an optional link
  to another part of the site. 
* The order of the products within the block should be controllable





  