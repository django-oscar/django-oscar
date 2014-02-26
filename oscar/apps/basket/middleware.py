from django.conf import settings
from django.core.signing import Signer, BadSignature
from django.utils.functional import SimpleLazyObject, empty

from oscar.core.loading import get_model
from oscar.core.loading import get_class

Applicator = get_class('offer.utils', 'Applicator')
Basket = get_model('basket', 'basket')
Selector = get_class('partner.strategy', 'Selector')

selector = Selector()


class BasketMiddleware(object):

    def process_request(self, request):
        request.cookies_to_delete = []

        # Load stock/price strategy and assign to request and basket
        strategy = selector.strategy(request=request, user=request.user)
        request.strategy = strategy

        def lazy_load_basket():
            basket = self.get_basket(request)
            basket.strategy = request.strategy

            request.basket = basket

            # Attach basket to the current request. Pricing policies in
            # apply_offers_to_basket may depend on it, so it needs to be done
            # before that is called
            self.ensure_basket_lines_have_stockrecord(basket)
            self.apply_offers_to_basket(request, basket)

            return basket

        request.basket = SimpleLazyObject(lazy_load_basket)

    def get_basket(self, request):
        """
        Return an open basket for this request
        """
        manager = Basket.open
        cookie_basket = self.get_cookie_basket(
            settings.OSCAR_BASKET_COOKIE_OPEN, request, manager)

        if hasattr(request, 'user') and request.user.is_authenticated():
            # Signed-in user: if they have a cookie basket too, it means
            # that they have just signed in and we need to merge their cookie
            # basket into their user basket, then delete the cookie
            try:
                basket, _ = manager.get_or_create(owner=request.user)
            except Basket.MultipleObjectsReturned:
                # Not sure quite how we end up here with multiple baskets
                # We merge them and create a fresh one
                old_baskets = list(manager.filter(owner=request.user))
                basket = old_baskets[0]
                for other_basket in old_baskets[1:]:
                    self.merge_baskets(basket, other_basket)

            # Assign user onto basket to prevent further SQL queries when
            # basket.owner is accessed.
            basket.owner = request.user

            if cookie_basket:
                self.merge_baskets(basket, cookie_basket)
                request.cookies_to_delete.append(
                    settings.OSCAR_BASKET_COOKIE_OPEN)
        elif cookie_basket:
            # Anonymous user with a basket tied to the cookie
            basket = cookie_basket
        else:
            # Anonymous user with no basket - we don't save the basket until
            # we need to.
            basket = Basket()
        return basket

    def merge_baskets(self, master, slave):
        """
        Merge one basket into another.

        This is its own method to allow it to be overridden
        """
        master.merge(slave, add_quantities=False)

    def process_response(self, request, response):
        # Delete any surplus cookies
        cookies_to_delete = getattr(request, 'cookies_to_delete', [])
        for cookie_key in cookies_to_delete:
            response.delete_cookie(cookie_key)

        if not hasattr(request, 'basket'):
            return response

        # If the basket was never initialized we can safely return
        if (isinstance(request.basket, SimpleLazyObject)
                and request.basket._wrapped is empty):
            return response

        # Check if we need to set a cookie. If the cookies is already available
        # but is set in the cookies_to_delete list then we need to re-set it.
        has_basket_cookie = (
            settings.OSCAR_BASKET_COOKIE_OPEN in request.COOKIES
            and settings.OSCAR_BASKET_COOKIE_OPEN not in cookies_to_delete)

        # If a basket has had products added to it, but the user is anonymous
        # then we need to assign it to a cookie
        if (request.basket.id and not request.user.is_authenticated()
                and not has_basket_cookie):
            cookie = self.get_basket_hash(request.basket.id)
            response.set_cookie(
                settings.OSCAR_BASKET_COOKIE_OPEN, cookie,
                max_age=settings.OSCAR_BASKET_COOKIE_LIFETIME, httponly=True)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            if response.context_data is None:
                response.context_data = {}
            if 'basket' not in response.context_data:
                response.context_data['basket'] = request.basket
            else:
                # Occasionally, a view will want to pass an alternative basket
                # to be rendered.  This can happen as part of checkout
                # processes where the submitted basket is frozen when the
                # customer is redirected to another site (eg PayPal).  When the
                # customer returns and we want to show the order preview
                # template, we need to ensure that the frozen basket gets
                # rendered (not request.basket).  We still keep a reference to
                # the request basket (just in case).
                response.context_data['request_basket'] = request.basket
        return response

    def get_cookie_basket(self, cookie_key, request, manager):
        """
        Looks for a basket which is referenced by a cookie.

        If a cookie key is found with no matching basket, then we add
        it to the list to be deleted.
        """
        basket = None
        if cookie_key in request.COOKIES:
            basket_hash = request.COOKIES[cookie_key]
            try:
                basket_id = Signer().unsign(basket_hash)
                basket = Basket.objects.get(pk=basket_id, owner=None,
                                            status=Basket.OPEN)
            except (BadSignature, Basket.DoesNotExist):
                request.cookies_to_delete.append(cookie_key)
        return basket

    def apply_offers_to_basket(self, request, basket):
        if not basket.is_empty:
            Applicator().apply(request, basket)

    def get_basket_hash(self, basket_id):
        return Signer().sign(basket_id)

    def ensure_basket_lines_have_stockrecord(self, basket):
        """
        Ensure each basket line has a stockrecord.

        This is to handle the backwards compatibility issue introduced in v0.6
        where basket lines began to require a stockrecord.
        """
        if not basket.id:
            return
        for line in basket.all_lines():
            if not line.stockrecord:
                self.ensure_line_has_stockrecord(basket, line)

    def ensure_line_has_stockrecord(self, basket, line):
        # Get details off line before deleting it
        product = line.product
        quantity = line.quantity
        options = []
        for attr in line.attributes.all():
            options.append({
                'option': attr.option,
                'value': attr.value})
        line.delete()

        # Attempt to re-add to basket with the appropriate stockrecord
        stock_info = basket.strategy.fetch_for_product(product)
        if stock_info.stockrecord:
            basket.add(product, quantity, options=options)
