=======================
Prices and availability
=======================

This page explains how prices and availability are determined in Oscar.  In
short, it seems quite complicated at first as there are several parts to it, but what
this buys is flexibility: buckets of it.

Overview
--------

Simpler e-commerce frameworks often tie prices to the product model directly:

.. code-block:: python

   >>> product = Product.objects.get(id=1)
   >>> product.price
   Decimal('17.99')

Oscar, on the other hand, distinguishes products from stockrecords and provides
a swappable 'strategy' component for selecting the appropriate stockrecord,
calculating prices and availability information.

.. code-block:: python

   >>> from oscar.apps.partner.strategy import Selector
   >>> product = Product.objects.get(id=1)
   >>> strategy = Selector().strategy()
   >>> info = strategy.fetch_for_product(product)

   # Availability information
   >>> info.availability.is_available_to_buy
   True
   >>> msg = info.availability.message
   >>> unicode(msg)
   u"In stock (58 available)"
   >>> info.availability.is_purchase_permitted(59)
   (False, u"A maximum of 58 can be bought")

   # Price information
   >>> info.price.excl_tax
   Decimal('17.99')
   >>> info.price.is_tax_known
   True
   >>> info.price.incl_tax
   Decimal('21.59')
   >>> info.price.tax
   Decimal('3.60')
   >>> info.price.currency
   'GBP'

The product model captures the core data about the product (title, description,
images) while a stockrecord represents fulfillment information for one
particular partner (number in stock, base price).  A product can have multiple
stockrecords although only one is selected by the strategy to determine pricing and
availability.

By using your own custom strategy class, a wide range of pricing, tax and
availability problems can be easily solved.

.. _strategy_class:

The strategy class
------------------

Oscar uses a 'strategy' object to determine product availability and pricing.  A
new strategy instance is assigned to the request by the basket middleware.  A
:class:`~oscar.apps.partner.strategy.Selector`
class determines the appropriate strategy for the
request.  By modifying the 
:class:`~oscar.apps.partner.strategy.Selector`
class, it's possible to return
different strategies for different customers.

Given a product, the strategy class is responsible for:

- Selecting a "pricing policy", an object detailing the prices of the product and whether tax is known.
- Selecting an "availability policy", an object responsible for
  availability logic (ie is the product available to buy) and customer
  messaging.
- Selecting the appropriate stockrecord to use for fulfillment.  If a product
  can be fulfilled by several fulfilment partners, then each will have their
  own stockrecord.

These three entities are wrapped up in a ``PurchaseInfo`` object, which is a
simple named tuple.  The strategy class provides ``fetch_for_product`` and
``fetch_for_parent`` methods which takes a product and returns a ``PurchaseInfo``
instance:

The strategy class is accessed in several places in Oscar's codebase.  In templates, a
``purchase_info_for_product`` template tag is used to load the price and availability
information into the template context:

.. code-block:: html+django

   {% load purchase_info_tags %}
   {% load currency_filters %}

   {% purchase_info_for_product request product as session %}

   <p>
   {% if session.price.is_tax_known %}
       Price is {{ session.price.incl_tax|currency:session.price.currency }}
   {% else %}
       Price is {{ session.price.excl_tax|currency:session.price.currency }} +
       tax
   {% endif %}
   </p>

Note that the ``currency`` template tag accepts a currency parameter from the
pricing policy.  
    
Also, basket instances have a strategy instance assigned so they can calculate
prices including taxes.  This is done automatically in the basket middleware.

This seems quite complicated...
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While this probably seems like quite an involved way of looking up a product's
price, it gives the developer an immense amount of flexibility.  Here's a few
examples of things you can do with a strategy class:

- Transact in multiple currencies.  The strategy
  class can use the customer's location to select a stockrecord from a local
  distribution partner which will be in the local currency of the customer.

- Elegantly handle different tax models.  A strategy can return prices including
  tax for a UK or European visitor, but without tax for US
  visitors where tax is only determined once shipping details are confirmed.

- Charge different prices to different customers.  A strategy can return a
  different pricing policy depending on the user/session.

- Use a chain of preferred partners for fulfillment.  A site could have many
  stockrecords for the same product, each from a different fulfillment partner.
  The strategy class could select the partner with the best margin and stock
  available.  When stock runs out with that partner, the strategy could
  seamlessly switch to the next best partner.

These are the kinds of problems that other e-commerce frameworks would struggle
with.  

API
~~~

All strategies subclass a common ``Base`` class:

.. autoclass:: oscar.apps.partner.strategy.Base
   :members: fetch_for_product, fetch_for_parent, fetch_for_line
   :noindex:

Oscar also provides a "structured" strategy class which provides overridable
methods for selecting the stockrecord, and determining pricing and availability
policies:

.. autoclass:: oscar.apps.partner.strategy.Structured
   :members:
   :noindex:

For most projects, subclassing and overriding the ``Structured`` base class
should be sufficient.  However, Oscar also provides mixins to easily compose the
appropriate strategy class for your domain.

Loading a strategy
------------------

Strategy instances are determined by the ``Selector`` class:

.. autoclass:: oscar.apps.partner.strategy.Selector
   :members:
   :noindex:

It's common to override this class so a custom strategy class can be returned.

.. _pricing_policies:

Pricing policies
----------------

A pricing policy is a simple class with several properties  Its job is to
contain all price and tax information about a product.

There is a base class that defines the interface a pricing policy should have:

.. autoclass:: oscar.apps.partner.prices.Base
   :members:
   :noindex:

There are also several policies that accommodate common scenarios:

.. automodule:: oscar.apps.partner.prices
   :members: Unavailable, FixedPrice 
   :noindex:

.. _availability_policies:

Availability policies
---------------------

Like pricing policies, availability policies are simple classes with several
properties and methods.  The job of an availability policy is to provide
availability messaging to show to the customer as well as methods to determine
if the product is available to buy.

The base class defines the interface:

.. autoclass:: oscar.apps.partner.availability.Base
   :members:
   :noindex:

There are also several pre-defined availability policies:

.. automodule:: oscar.apps.partner.availability
   :members: Unavailable, Available, StockRequired
   :noindex:

Strategy mixins
---------------

Oscar also ships with several mixins which implement one method of the
``Structured`` strategy.  These allow strategies to be easily
composed from re-usable parts:

.. automodule:: oscar.apps.partner.strategy
   :members: UseFirstStockRecord, StockRequired, NoTax, FixedRateTax,
             DeferredTax
   :noindex:

Default strategy
----------------

Oscar's default ``Selector`` class returns a ``Default`` strategy built from
the strategy mixins:

.. code-block:: python

   class Default(UseFirstStockRecord, StockRequired, NoTax, Structured):
       pass

The behaviour of this strategy is:

- Always picks the first stockrecord (this is backwards compatible with
  Oscar<0.6 where a product could only have one stockrecord).
- Charge no tax.
- Only allow purchases where there is appropriate stock (eg no back-orders).

How to use
----------

There's lots of ways to use strategies, pricing and availability policies to
handle your domain's requirements.

The normal first step is provide your own ``Selector`` class which returns a custom
strategy class.  Your custom strategy class can be composed of the above mixins
or your own custom logic.

Example 1: UK VAT
~~~~~~~~~~~~~~~~~

Here's an example ``strategy.py`` module which is used to charge VAT on prices.

.. code-block:: python

    # myproject/partner/strategy.py

    from oscar.apps.partner import strategy, prices


    class Selector(object):
        """
        Custom selector to return a UK-specific strategy that charges VAT
        """

        def strategy(self, request=None, user=None, **kwargs):
            return UKStrategy()


    class IncludingVAT(strategy.FixedRateTax):
        """
        Price policy to charge VAT on the base price
        """
        # We can simply override the tax rate on the core FixedRateTax.  Note
        # this is a simplification: in reality, you might want to store tax
        # rates and the date ranges they apply in a database table.  Your
        # pricing policy could simply look up the appropriate rate.
        rate = D('0.20')


    class UKStrategy(strategy.UseFirstStockRecord, IncludingVAT, 
                     strategy.StockRequired, strategy.Structured):
        """
        Typical UK strategy for physical goods.  

        - There's only one warehouse/partner so we use the first and only stockrecord 
        - Enforce stock level.  Don't allow purchases when we don't have stock.
        - Charge UK VAT on prices.  Assume everything is standard-rated.
        """

Example 2: US sales tax
~~~~~~~~~~~~~~~~~~~~~~~

Here's an example ``strategy.py`` module which is suitable for use in the US
where taxes can't be calculated until the shipping address is known.  You
normally need to use a 3rd party service to determine taxes - details omitted
here.

.. code-block:: python

    from oscar.apps.partner import strategy, prices


    class Selector(object):
        """
        Custom selector class to returns a US strategy
        """

        def strategy(self, request=None, user=None, **kwargs):
            return USStrategy()


    class USStrategy(strategy.UseFirstStockRecord, strategy.DeferredTax, 
                     strategy.StockRequired, strategy.Structured):
        """
        Typical US strategy for physical goods.  Note we use the ``DeferredTax``
        mixin to ensure prices are returned without tax.

        - Use first stockrecord
        - Enforce stock level
        - Taxes aren't known for prices at this stage
        """
