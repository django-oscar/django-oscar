===========================
How to apply tax exemptions
===========================

Problem
=======
The tax a customer pays depends on the shipping address of his/her
order.  

Solution
========
Use custom basket middleware to set the tax status of the basket.

The default Oscar basket middleware is::

    'oscar.apps.basket.middleware.BasketMiddleware'

To alter the tax behaviour, replace this class with one within your own project
that subclasses Oscar's and extends the ``get_basket`` method.  For example, use
something like::

    from oscar.apps.basket.middleware import BasketMiddleware
    from oscar.apps.checkout.utils import CheckoutSessionData

    class MyBasketMiddleware(BasketMiddleware):
        
        def get_basket(self, request):
            basket = super(MyBasketMiddleware, self).get_basket(request)
            if self.is_tax_exempt(request):
                basket.set_as_tax_exempt()
            return basket

        def is_tax_exempt(self, request):
            country = self.get_shipping_address_country(request)
            if country is None:
                return False
            return country.iso_3166_1_a2 not in ('GB',)

        def get_shipping_address_country(self, request):
            session = CheckoutSessionData(request)
            if not session.is_shipping_address_set():
                return None
            addr_id = session.shipping_user_address_id()
            if addr_id:
                # User shipping to address from address book
                return UserAddress.objects.get(id=addr_id).country
            else:
                fields = session.new_shipping_address_fields()
        
Here we are using the checkout session wrapper to check if the user has set a
shipping address.  If they have, we extract the country and check its ISO
3166 code.

It is straightforward to extend this idea to apply custom tax exemptions to the
basket based of different criteria.