from contextlib import contextmanager
from itertools import chain
import logging

from django.db.models import Q
from django.utils.timezone import now

from oscar.core.loading import get_model
from oscar.apps.offer import results

ConditionalOffer = get_model('offer', 'ConditionalOffer')

logger = logging.getLogger('oscar.offers')


class OfferApplicationError(Exception):
    pass


class Line(object):
    """
    A product and quantity used in offer discount calculation.
    """
    def __init__(self, reference, product, stockrecord, quantity, price):
        self.reference = reference
        self.product = product
        self.stockrecord = stockrecord
        self.quantity = quantity
        self.price = price
        self.benefits = []

    def add_benefit(self, transaction_id, benefit, quantity, discount):
        self.benefits.append((transaction_id, benefit, quantity, discount))

    def remove_benefits(self, transaction_id):
        self.benefits = filter(
            lambda (c_transaction_id, condition, quantity, discount):
            c_transaction_id != transaction_id,
            self.benefits)

    def quantity_with_benefit(self, benefit):
        # django-1.7: When we drop support for Django < 1.7 we can change
        # b[1] is benefit to b[1] == benefit and thus allow separate instances
        # representing the same database row to pass the test. For now we need
        # unsaved instances to be different for the tests. In Django-1.7 both
        # hold true with ==.
        # https://github.com/django/django/commit/6af05e7a0f0e4604d6a67899acaa99d73ec0dfaa  # noqa
        return sum(b[2] for b in self.benefits
                   if b[1] is benefit)

    def quantity_with_benefits(self):
        def maximum(iterable, default):
            try:
                return max(iterable)
            except ValueError:
                return default

        return max(maximum((b[2] for b in self.benefits
                            if b[1].can_apply_with_other_benefits), 0),
                   sum(b[2] for b in self.benefits
                       if not b[1].can_apply_with_other_benefits))

    def quantity_without_benefits(self):
        return self.quantity - self.quantity_with_benefits()

    def quantity_with_greedy_benefits(self):
        return sum(b[2] for b in self.benefits
                   if not b[1].can_apply_with_other_benefits)

    def quantity_available_for_benefit(self, benefit):
        if not benefit.can_apply_with_other_benefits:
            return self.quantity - self.quantity_with_greedy_benefits()
        return self.quantity - self.quantity_with_benefit(benefit)

    def is_available_for_benefit(self, benefit):
        return self.quantity_available_for_benefit(benefit) > 0

    def get_discount_value(self):
        return sum(b[3] for b in self.benefits)

    @property
    def discounted_price(self):
        return self.price - self.get_discount_value()


class SetOfLines(object):
    @classmethod
    def from_basket(cls, basket):
        return cls([
            Line(line.line_reference, line.product, line.stockrecord,
                 line.quantity, line.unit_effective_price)
            for line in basket.all_lines()])

    def __init__(self, lines):
        self.lines = list(lines)
        self.transaction_id = 0

    def __iter__(self):
        return self.lines.__iter__()

    def __len__(self):
        return len(self.lines)

    def add_line(self, line):
        self.lines.append(line)

    @contextmanager
    def begin_transaction(self):
        set_of_lines = self

        self.transaction_id += 1

        class Transaction(object):
            def rollback(self):
                set_of_lines.rollback_transaction()

        yield Transaction()

    def rollback_transaction(self):
        """
        Remove all conditions and benefits with the current transaction id.
        """
        for line in self.lines:
            line.remove_benefits(self.transaction_id)

    def mark_for_benefit(self, line, benefit, quantity, discount):
        """
        Mark `quantity` items of `line` for a discount amount of `discount`
        from `benefit`.
        """
        if discount == 0:
            return

        line.add_benefit(self.transaction_id, benefit, quantity, discount)

    def get_lines_available_for_benefit(self, benefit):
        """
        Return only those lines that can be used to satisfy a condition.
        """
        # We sort lines to be cheapest first to ensure consistent applications
        return sorted(
            [line for line in self.lines
             if (line.stockrecord
                 and line.price
                 and line.product.is_discountable
                 and line.is_available_for_benefit(benefit))],
            key=lambda line: line.price)

    @property
    def num_items_with_benefit(self):
        return sum(line.quantity_with_benefits() for line in self.lines)

    @property
    def num_items_without_benefit(self):
        return sum(line.quantity_without_benefits() for line in self.lines)

    def get_line_by_reference(self, reference):
        for line in self.lines:
            if line.reference == reference:
                return line


class Applicator(object):

    def apply(self, basket, user=None, request=None):
        """
        Apply all relevant offers to the given basket.

        The request is passed too as sometimes the available offers
        are dependent on the user (eg session-based offers).
        """
        offers = self.get_offers(basket, user, request)
        self.apply_offers_to_basket(basket, offers)

    def apply_offers_to_basket(self, basket, offers):
        set_of_lines = SetOfLines.from_basket(basket)

        applications = self.apply_offers(set_of_lines, offers, basket.owner)
        basket_lines_by_ref = {line.line_reference: line
                               for line in basket.all_lines()}
        for line in set_of_lines:
            basket_lines_by_ref[line.reference].discount(
                line.get_discount_value(), line.quantity_with_benefits(),
                incl_tax=True)
        # Store this list of discounts with the basket so it can be
        # rendered in templates
        basket.offer_applications = applications

    def apply_offers(self, set_of_lines, offers, user=None):
        applications = results.OfferApplications()
        for offer in offers:
            num_applications = 0
            # Keep applying the offer until either
            # (a) We reach the max number of applications for the offer.
            # (b) The benefit can't be applied successfully.
            while num_applications < offer.get_max_applications(user):
                result = offer.apply_benefit(set_of_lines)
                num_applications += 1
                if not result.is_successful:
                    break
                applications.add(offer, result)
                if result.is_final:
                    break

        return applications

    def get_offers(self, basket, user=None, request=None):
        """
        Return all offers to apply to the basket.

        This method should be subclassed and extended to provide more
        sophisticated behaviour.  For instance, you could load extra offers
        based on the session or the user type.
        """
        self._request = request

        site_offers = self.get_site_offers()
        basket_offers = self.get_basket_offers(basket, user)
        user_offers = self.get_user_offers(user)
        session_offers = self.get_session_offers(request)

        return list(sorted(chain(
            session_offers, basket_offers, user_offers, site_offers),
            key=lambda o: o.priority, reverse=True))

    def _get_available_offers(self):
        cutoff = now()
        date_based = Q(
            Q(start_datetime__lte=cutoff),
            Q(end_datetime__gte=cutoff) | Q(end_datetime=None),
        )

        nondate_based = Q(start_datetime=None, end_datetime=None)

        qs = ConditionalOffer.objects.filter(
            date_based | nondate_based,
            status=ConditionalOffer.OPEN)
        # Using select_related with the condition/benefit ranges doesn't
        # seem to work.  I think this is because both the related objects
        # have the FK to range with the same name.
        return qs.select_related('condition', 'benefit', 'benefit__range')

    def get_available_offers(self):
        if self._request is None:
            return self._get_available_offers()

        if not hasattr(self._request, '_available_offers'):
            self._request._available_offers = self._get_available_offers()

        return self._request._available_offers

    def get_site_offers(self):
        """
        Return site offers that are available to all users
        """
        return [offer for offer in self.get_available_offers()
                if offer.offer_type == ConditionalOffer.SITE]

    def get_basket_offers(self, basket, user):
        """
        Return basket-linked offers such as those associated with a voucher
        code
        """
        offers = []
        if not basket.id or not user:
            return offers

        for voucher in basket.vouchers.all():
            is_available_to_user, _ = voucher.is_available_to_user(user)
            if voucher.is_active() and is_available_to_user:
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
