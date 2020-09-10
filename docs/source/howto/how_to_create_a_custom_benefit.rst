==============================
How to create a custom benefit
==============================

Oscar ships with several offer benefits for building offers.  There are three
types:

* Basket discounts.  These lead to a discount off the price of items in your
  basket.

* Shipping discounts.

* Post-order actions.  These are benefits that don't affect your order total but
  trigger some action once the order is placed.  For instance, if your site
  supports loyalty points, you might create an offer that gives 200 points when
  a certain product is bought.

Oscar also lets you create your own benefits for use in offers.

Custom benefits
---------------

A custom benefit can be used by creating a benefit class and registering it so
it is available to be used.

A benefit class must be a proxy class and have the following methods::

    from oscar.apps.offer import models


    class MyCustomBenefit(models.Benefit):

        class Meta:
            proxy = True

        @property
        def name(self):
            return "My Custom Benefit"

        @property
        def description(self):
            """
            Describe what the benefit does.

            This is used in the dashboard when selecting benefits for offers.
            """

        def apply(self, basket, condition, offer):
            """
            Apply the benefit to the passed basket and mark the appropriate
            items as consumed.

            The condition and offer are passed as these are sometimes required
            to implement the correct consumption behaviour.

            Should return an instance of
            ``oscar.apps.offer.models.ApplicationResult``
            """

        def apply_deferred(self, basket, order, application):
            """
            Perform a 'post-order action' if one is defined for this benefit

            Should return a message indicating what has happened.  This will be
            stored with the order to provide audit of post-order benefits.
            """

As noted in the docstring, the ``apply`` method must return an instance of
``oscar.apps.offer.models.ApplicationResult``.  There are three subclasses
provided:

    * ``oscar.apps.offer.models.BasketDiscount``. This takes an amount as it's
      constructor parameter.

    * ``oscar.apps.offer.models.ShippingDiscount``. This indicates that the
      benefit affects the shipping charge.

    * ``oscar.apps.offer.models.PostOrderAction``. This indicates that the
      benefit does nothing to the order total, but does fire an action once the
      order has been placed.  It takes a single ``description`` parameter to its
      constructor which is a message that describes what action will be taken
      once the order is placed.

Here's an example of a post-order action benefit::

    from oscar.apps.offer import models

    class ChangesCustomersName(models.Benefit):

        class Meta:
            proxy = True

        name = description = "Changes customer's name"

        def apply(self, basket, condition, offer):
            # We need to mark all items from the matched condition as 'consumed'
            # so that they are unavailable to be used with other offers.
            condition.consume_items(basket, ())
            return models.PostOrderAction(
                "You will have your name changed to Barry!")

        def apply_deferred(self, basket, order, application):
            if basket.owner:
                basket.owner.first_name = "Barry"
                basket.owner.save()
                return "Your name has been changed to Barry!"
            return "We were unable to change your name as you are not signed in"

Create benefit instance
-------------------------

To make this benefit available to be used in offers, do the following::

    from oscar.apps.offer.custom import create_benefit

    create_benefit(ChangesCustomersName)

Now you should see this benefit in the dashboard when creating/updating an offer.

Deploying custom benefits
---------------------------

To avoid manual steps in each of your test/stage/production environments, use
Django `data migrations`_ to create benefits.

.. _`data migrations`: https://docs.djangoproject.com/en/stable/topics/migrations/#data-migrations
