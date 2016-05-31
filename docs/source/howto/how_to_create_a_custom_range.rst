============================
How to create a custom range
============================

Oscar ships with a range model that represents a set of products from your
catalogue.  Using the dashboard, this can be configured to be:

1.  The whole catalogue
2.  A subset of products selected by ID/SKU (CSV uploads can be used to do this)
3.  A subset of product categories

Often though, a shop may need merchant-specific ranges such as:

*  All products subject to reduced-rate VAT
*  All books by a Welsh author
*  DVDs that have an exclamation mark in the title

These are contrived but you get the picture.

Custom range interface
----------------------

A custom range must:

* have a ``name`` attribute
* have a ``contains_product`` method that takes a product instance and return a
  boolean
* have a ``num_products`` method that returns the number of products in the
  range or ``None`` if such a query would be too expensive.
* have an ``all_products`` method that returns a queryset of all products in the
  range.

Example::

    class ExclamatoryProducts(object):
        name = "Products including a '!'"

        def contains_product(self, product):
            return "!" in product.title

        def num_products(self):
            return self.all_products().count()

        def all_products(self):
            return Product.objects.filter(title__icontains="!")

Create range instance
---------------------

To make this range available to be used in offers, do the following::

    from oscar.apps.offer.custom import create_range

    create_range(ExclamatoryProducts)

Now you should see this range in the dashboard for ranges and offers.  Custom
ranges are not editable in the dashboard but can be deleted.

Deploying custom ranges
-----------------------

To avoid manual steps in each of your test/stage/production environments, use
South's `data migrations`_ to create ranges.

.. _`data migrations`: https://south.readthedocs.io/en/latest/tutorial/part3.html#data-migrations
