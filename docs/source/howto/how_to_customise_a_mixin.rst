========================
How to customise a mixin
========================

This How-to describes how to customise a mixin to create some special behaviour.
It is an advanced usage of Oscar and builds upon the steps described in
:doc:`/topics/customisation` and :doc:`/howto/how_to_customise_a_view`. Please read both documents
thoroughly and ensure that you've:

* Created a Python module with the same label
* Added it as Django app to ``INSTALLED_APPS``
* Used custom ``app.py``
* Created a subclass of the view that uses the mixin you want to customize

Only then you can create a subclass of the mixin and customise the behaviour.

Example: Custom behaviour when a successful order is placed
------------------------------------------------------------

Let's create something useful. Say you want to customize the behaviour Oscar does when a customer
places a successful order.
This behaviour is defined as `handle_successful_order` function in
`oscar.apps.checkout.mixins.OrderPlacementMixin`.

To customize that, you should do the obvious steps first, create a `checkout` module and add it
to ``INSTALLED_APPS``. After that, create the customized mixin in `mixins.py` file in your module::

    # myproject/checkout/mixins.py
    from oscar.apps.checkout.mixins import OrderPlacementMixin as CoreOrderPlacementMixin

    class OrderPlacementMixin(CoreOrderPlacementMixin):
        def handle_successful_order(self, order):
            # Some custom behaviour goes here

            return super(OrderPlacementMixin, self).handle_successful_order(order)

That mixin is used by `oscar.apps.checkout.views.PaymentDetailsView` view, so create a new
view in ``myproject.checkout.views`` that subclasses that core view::

    # myproject/checkout/views.py
    from oscar.apps.checkout.views import PaymentDetailsView as CorePaymentDetailsView

    class PaymentDetailsView(CorePaymentDetailsView):
        pass

`pass` is used since we don't want to override anything in the view class itself, we only
want to inherit the new mixin we created. Be aware of the order of multi inheritance, since
it has a vital role here::

    # myproject/checkout/views.py
    from oscar.apps.checkout.views import PaymentDetailsView as CorePaymentDetailsView

    from myproject.checkout.mixins import OrderPlacementMixin

    class PaymentDetailsView(CorePaymentDetailsView, OrderPlacementMixin):
        pass


Now hook the new view up in your local ``app.py``::

    # myproject/checkout/app.py
    from oscar.apps.checkout.app import CheckoutApplication as CoreCheckoutApplication

    from myproject.checkout.views import PaymentDetailsView

    class CheckoutApplication(CoreCheckoutApplication):
        payment_details_view = PaymentDetailsView

    application = CheckoutApplication()
