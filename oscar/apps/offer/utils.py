from decimal import Decimal
from itertools import chain
import logging

from django.db.models import get_model

ConditionalOffer = get_model('offer', 'ConditionalOffer')

logger = logging.getLogger('oscar.offers')


class OfferApplicationError(Exception):
    pass


class Applicator(object):
    """
    Apply offers to a basket.
    """
    def apply(self, request, basket):
        """
        Apply all relevant offers to the given basket.

        The request and user are passed too as sometimes the available offers
        are dependent on the user (eg session-based offers).
        """
        # Flush any existing discounts to make sure they are recalculated
        # correctly
        basket.remove_discounts()

        offers = self.get_offers(request, basket)
        logger.debug("Found %d offers to apply to basket %d",
                     len(offers), basket.id)
        discounts = self.get_basket_discounts(basket, offers)

        # Store this list of discounts with the basket so it can be
        # rendered in templates
        basket.set_discounts(list(discounts.values()))

    def get_basket_discounts(self, basket, offers):
        discounts = {}
        for offer in offers:
            # For each offer, we keep trying to apply it until the
            # discount is 0
            applications = 0
            while applications < offer.get_max_applications(basket.owner):
                discount = offer.apply_benefit(basket)
                applications += 1
                logger.debug("Found discount %.2f for basket %d from offer %d",
                             discount, basket.id, offer.id)
                if discount > 0:
                    if offer.id not in discounts:
                        discounts[offer.id] = {'name': offer.name,
                                               'offer': offer,
                                               'voucher': offer.get_voucher(),
                                               'freq': 0,
                                               'discount': Decimal('0.00')}
                    discounts[offer.id]['discount'] += discount
                    discounts[offer.id]['freq'] += 1
                else:
                    break

        logger.debug("Finished applying offers to basket %d", basket.id)
        return discounts

    def get_offers(self, request, basket):
        """
        Return all offers to apply to the basket.

        This method should be subclassed and extended to provide more
        sophisticated behaviour.  For instance, you could load extra offers
        based on the session or the user type.
        """
        site_offers = self.get_site_offers()
        basket_offers = self.get_basket_offers(basket, request.user)
        user_offers = self.get_user_offers(request.user)
        session_offers = self.get_session_offers(request)

        return list(chain(
            session_offers, basket_offers, user_offers, site_offers))

    def get_site_offers(self):
        """
        Return site offers that are available to all users
        """
        date_based_offers = ConditionalOffer.active.filter(
            offer_type=ConditionalOffer.SITE,
            status=ConditionalOffer.OPEN)
        nondate_based_offers = ConditionalOffer.objects.filter(
            offer_type=ConditionalOffer.SITE,
            status=ConditionalOffer.OPEN,
            start_date=None, end_date=None)
        return list(chain(date_based_offers, nondate_based_offers))

    def get_basket_offers(self, basket, user):
        """
        Return basket-linked offers such as those associated with a voucher
        code
        """
        offers = []
        if not basket.id:
            return offers

        for voucher in basket.vouchers.all():
            if voucher.is_active() and voucher.is_available_to_user(user):
                basket_offers = voucher.offers.all()
                for offer in basket_offers:
                    offer.set_voucher(voucher)
                offers = list(chain(offers, basket_offers))
        return offers

    def get_user_offers(self, user):
        """
        Returns offers linked to this particular user.

        Eg: student users might get 25% off
        """
        return []

    def get_session_offers(self, request):
        """
        Returns temporary offers linked to the current session.

        Eg: visitors coming from an affiliate site get a 10% discount
        """
        return []
