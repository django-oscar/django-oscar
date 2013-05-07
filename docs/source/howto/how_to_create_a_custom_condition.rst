======================================
How to create a custom offer condition
======================================

Oscar ships with several condition models that can be used to build offers.
However, occasionally a custom condition can be useful.  Oscar lets you build a
custom condition class and register it so that it is available for building
offers.

Custom condition interface
--------------------------

Custom condition classes must be proxy models, subclassing Oscar's main
Condition class.

At a minimum, a custom condition must:

* have a ``name`` attribute
* have an ``is_satisified`` method that takes a basket instance and returns a
  boolean

It can also implement:

* a ``can_apply_condition`` method that takes a product instance and returns a
  boolean depending on whether the condition is applicable to the product.

* a ``consume_items`` method that marks basket items as consumed once the
  condition has been met.

* a ``get_upsell_message`` method that returns a message for the customer,
  letting them know what they would need to do to qualify for this offer.

* a ``is_partially_satisfied`` method that tests to see if the customer's basket
  partially satisfies the condition (ie when you might want to show them an
  upsel message)

Silly example::

    from oscar.apps.offer import models

    class BasketOwnerCalledBarry(models.Condition):
        name = "User must be called barry"

        class Meta:
            proxy = True

        def is_satisfied(self, basket):
            if not basket.owner:
                return False
            return basket.owner.first_name.lower() == 'barry'

Create condition instance
-------------------------

To make this condition available to be used in offers, do the following::

    from oscar.apps.offer.custom import create_condition

    create_range(BasketOwnerCalledBarry)

Now you should see this range in the dashboard when creating/updating an offer.

Deploying custom conditions
---------------------------

To avoid manual steps in each of your test/stage/production environments, use
South's `data migrations`_ to create conditions.

.. _`data migrations`: http://south.readthedocs.org/en/latest/tutorial/part3.html#data-migrations