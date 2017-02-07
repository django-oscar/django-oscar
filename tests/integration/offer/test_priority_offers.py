import mock
import datetime

from django.test import TestCase
from django.utils import timezone

from oscar.core.loading import get_model
from oscar.apps.offer import utils
from oscar.test import factories

Voucher = get_model('voucher', 'Voucher')


class TestPriorityOffers(TestCase):
    def test_site_offers_are_ordered(self):
        factories.create_offer(name="A", priority=0)
        factories.create_offer(name="B", priority=7)
        factories.create_offer(name="C", priority=5)
        factories.create_offer(name="D", priority=7)
        factories.create_offer(name="E", priority=1)

        offers = utils.Applicator().get_site_offers()
        ordered_names = [offer.name for offer in offers]
        self.assertEqual(["B", "D", "C", "E", "A"], ordered_names)

    def test_basket_offers_are_ordered(self):
        voucher = Voucher.objects.create(
            name="Test voucher",
            code="test",
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + datetime.timedelta(days=12))

        voucher.offers = [
            factories.create_offer(name="A", priority=0),
            factories.create_offer(name="B", priority=7),
            factories.create_offer(name="C", priority=5),
            factories.create_offer(name="D", priority=7),
            factories.create_offer(name="E", priority=1),
        ]

        basket = factories.create_basket()
        user = mock.Mock()

        # Apply voucher to basket
        basket.vouchers.add(voucher)

        offers = utils.Applicator().get_basket_offers(basket, user)
        ordered_names = [offer.name for offer in offers]
        self.assertEqual(["B", "D", "C", "E", "A"], ordered_names)
