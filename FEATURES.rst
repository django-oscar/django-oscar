========
Features
========

Below is a list of required features for oscar, together with a brief spec for
what they should implement.  If you're looking for something to do, please have a
go at one of the below.


Reviews and voting
------------------

Create a new ``oscar.reviews`` app which provides reviews and voting functionality. 

* Each product can have reviews attached to it.  Each review has a title, a body and a score from 1-5.
* Signed in users can always submit reviews, anonymous users can only submit reviews if a setting 
  ``OSCAR_ALLOW_ANON_REVIEWS`` is set to true - it should default to false.
* If anon users can submit reviews, then we require their name, email address and an (optional) URL.
* By default, reviews must be approved before they are live.  However, if a setting ``OSCAR_MODERATE_REVIEWS``
  is set to false, then they don't need moderation.
* The product page should have a review form on it, any errors in the submission will be shown on the same product page
* The product page will show the most recent 5 reviews with a link to browse all reviews for that product.
* The URL for browsing a products offers should be the normal product URL with /reviews appended at the end
* The product page should show the average score based on the reviews 
* The review browsing page should allow reviews to be sorted by score, or recency.
* Each review should have a permalink, ie it has its own page.
* Each reviews can be voted up or down by other users
* Only signed in users can vote
* A user can only vote once on each product once

It might be possible to use the Django comments framework for this.


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


Wishlists
---------

Create a new ``oscar.wishlist`` app similar to the basket app. 

* A wishlist is simply a list of products
* Wishlist products do not have quantities
* Only signed in users can have wishlists
* A user can only have one wishlist (for now)
* A wishlist can either be public or private
* A user can add a product to their wishlist from a product page - after adding they are redirected
  to their wishlist management page but with a link back to the page they just came from.
* The wishlist management should have URL /wishlist
* On the wishlist management page:
  - you can add the item to your normal basket or remove it from your wishlist 
  - you can make your list public or private
  - you can empty your whole wishlist
  
The view functions for this app should be v similar to the basket ones.  Also have a look at Amazons for
guidance.


CurrencyField
-------------

Lots of models have a currency field but the field attributes are duplicated each time.  This could be
simplified if we had a currency field class.  

* This should set the correct decimal settings and support a default value


Extended URL field
------------------

Pods, banners and merchandising blocks need to link to either an external URL or an internal
one (eg /fiction-books/).  The current URLField only supports external ones.  Write a new type 
of field class that allows internal URLs too. 


  