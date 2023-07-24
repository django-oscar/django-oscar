from collections import defaultdict, namedtuple

from django.contrib import messages
from django.template.loader import render_to_string

from oscar.core.loading import get_class, get_model
from oscar.core.decorators import deprecated

Applicator = get_class("offer.applicator", "Applicator")
ConditionalOffer = get_model("offer", "ConditionalOffer")

DiscountApplication = namedtuple(
    "DiscountApplication", ["amount", "quantity", "incl_tax", "offer"]
)


class BasketMessageGenerator(object):
    new_total_template_name = "oscar/basket/messages/new_total.html"
    offer_lost_template_name = "oscar/basket/messages/offer_lost.html"
    offer_gained_template_name = "oscar/basket/messages/offer_gained.html"

    def get_new_total_messages(self, basket, include_buttons=True):
        new_total_messages = []
        # We use the 'include_buttons' parameter to determine whether to show the
        # 'Checkout now' buttons.  We don't want to show these on the basket page.
        msg = render_to_string(
            self.new_total_template_name,
            {"basket": basket, "include_buttons": include_buttons},
        )
        new_total_messages.append((messages.INFO, msg))

        return new_total_messages

    def get_offer_lost_messages(self, offers_before, offers_after):
        offer_messages = []
        for offer_id in set(offers_before).difference(offers_after):
            offer = offers_before[offer_id]
            msg = render_to_string(self.offer_lost_template_name, {"offer": offer})
            offer_messages.append((messages.WARNING, msg))
        return offer_messages

    def get_offer_gained_messages(self, offers_before, offers_after):
        offer_messages = []
        for offer_id in set(offers_after).difference(offers_before):
            offer = offers_after[offer_id]
            msg = render_to_string(self.offer_gained_template_name, {"offer": offer})
            offer_messages.append((messages.SUCCESS, msg))
        return offer_messages

    def get_offer_messages(self, offers_before, offers_after):
        offer_messages = []
        offer_messages.extend(self.get_offer_lost_messages(offers_before, offers_after))
        offer_messages.extend(
            self.get_offer_gained_messages(offers_before, offers_after)
        )
        return offer_messages

    def get_messages(self, basket, offers_before, offers_after, include_buttons=True):
        message_list = []
        message_list.extend(self.get_offer_messages(offers_before, offers_after))
        message_list.extend(self.get_new_total_messages(basket, include_buttons))
        return message_list

    def apply_messages(self, request, offers_before):
        """
        Set flash messages triggered by changes to the basket
        """
        # Re-apply offers to see if any new ones are now available
        request.basket.reset_offer_applications()
        Applicator().apply(request.basket, request.user, request)
        offers_after = request.basket.applied_offers()

        for level, msg in self.get_messages(
            request.basket, offers_before, offers_after
        ):
            messages.add_message(request, level, msg, extra_tags="safe noicon")


class LineOfferConsumer(object):
    """
    facade for marking basket lines as consumed by
    any or a specific offering.

    historically oscar marks a line as consumed if any
    offer is applied to it, but more complicated scenarios
    are possible if we mark the line as being consumed by
    specific offers.

    this allows combining i.e. multiple vouchers, vouchers
    with special session discounts, etc.
    """

    def __init__(self, line):
        self._line = line
        self._offers = dict()
        self._affected_quantity = 0
        self._consumptions = defaultdict(int)

    def _cache(self, offer):
        self._offers[offer.pk] = offer

    def _update_affected_quantity(self, quantity):
        available = int(self._line.quantity - self._affected_quantity)
        num_consumed = min(available, quantity)
        self._affected_quantity += num_consumed
        return num_consumed

    # public
    def consume(self, quantity: int, offer=None):
        """
        mark a basket line as consumed by an offer

        :param int quantity: the number of items on the line affected
        :param offer: the offer to mark the line
        :type offer: ConditionalOffer or None
        :return: the number of items actually consumed
        :rtype: int

        if offer is None, the specified quantity of items on this
        basket line is consumed for *any* offer, else only for the
        specified offer.
        """
        if offer:
            self._cache(offer)
            available = self.available(offer)

        num_consumed = self._update_affected_quantity(quantity)
        if offer:
            num_consumed = min(available, quantity)
            self._consumptions[offer.pk] += num_consumed
        return num_consumed

    @deprecated
    def consumed(self, offer=None):
        return self.num_consumed(offer)

    def num_consumed(self, offer=None):
        """
        check how many items on this line have been
        consumed by an offer

        :param offer: the offer to check
        :type offer: ConditionalOffer or None
        :return: the number of items marked as consumed
        :rtype: int

        if offer is not None, only the number of items marked
        with the specified ConditionalOffer are returned

        """
        if not offer:
            return self._affected_quantity
        return int(self._consumptions[offer.pk])

    @property
    def consumers(self):
        return [x for x in self._offers.values() if self.num_consumed(x)]

    def available(self, offer=None) -> int:
        """
        check how many items are available for offer

        :param offer: the offer to check
        :type offer: ConditionalOffer or None
        :return: the number of items available for offer
        :rtype: int
        """
        max_affected_items = self._line.quantity

        if offer and isinstance(offer, ConditionalOffer):
            applied = [x for x in self.consumers if x != offer]

            if offer.exclusive:
                for a in applied:
                    if a.exclusive:
                        if any(
                            [
                                a.priority > offer.priority,
                                a.priority == offer.priority and a.id != offer.id,
                            ]
                        ):
                            # Exclusive offers cannot be applied if any other exclusive
                            # offer with higher priority is active already.
                            max_affected_items = max_affected_items - self.num_consumed(
                                a
                            )
                            if max_affected_items == 0:
                                return 0

                    else:
                        # Exclusive offers cannot be applied if any other offers are
                        # active already.
                        return 0

            # find any *other* exclusive offers
            elif any([x.exclusive for x in applied]):
                return 0

            # check for applied offers allowing restricted combinations
            for x in applied:
                check = offer.combinations.count() or x.combinations.count()
                if check and offer not in x.combined_offers:
                    return 0

        return max_affected_items - self.num_consumed(offer)


class LineDiscountRegistry(LineOfferConsumer):
    def __init__(self, line):
        super().__init__(line)
        self._discounts = []
        self._discount_excl_tax = None
        self._discount_incl_tax = None

    def discount(self, amount, quantity, incl_tax=True, offer=None):
        self._discounts.append(DiscountApplication(amount, quantity, incl_tax, offer))
        self.consume(quantity, offer=offer)
        if incl_tax:
            self._discount_incl_tax = None
        else:
            self._discount_excl_tax = None

    @property
    def excl_tax(self):
        if self._discount_excl_tax is None:
            self._discount_excl_tax = sum(
                [d.amount for d in self._discounts if not d.incl_tax], 0
            )
        return self._discount_excl_tax

    @property
    def incl_tax(self):
        if self._discount_incl_tax is None:
            self._discount_incl_tax = sum(
                [d.amount for d in self._discounts if d.incl_tax], 0
            )
        return self._discount_incl_tax

    @property
    def total(self):
        return sum([d.amount for d in self._discounts], 0)

    def all(self):
        return self._discounts

    def __iter__(self):
        return iter(self._discounts)
