import datetime

from django.test import TestCase
from django.utils.timezone import now

from oscar.apps.dashboard.offers import forms
from oscar.apps.offer.models import ConditionalOffer
from oscar.test.factories import ConditionalOfferFactory, VoucherFactory


class TestMetaDataForm(TestCase):
    def test_changing_offer_type_for_voucher_offer_without_vouchers(self):
        offer = ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER)
        data = {
            "name": offer.name,
            "description": offer.description,
            "offer_type": ConditionalOffer.SITE,
        }
        form = forms.MetaDataForm(data, instance=offer)
        self.assertTrue(form.is_valid())

    def test_changing_offer_type_for_voucher_offer_with_vouchers(self):
        offer = ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER)
        VoucherFactory().offers.add(offer)
        data = {
            "name": offer.name,
            "description": offer.description,
            "offer_type": ConditionalOffer.SITE,
        }
        form = forms.MetaDataForm(data, instance=offer)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["offer_type"][0],
            "This can only be changed if it has no vouchers attached to it",
        )


class TestRestrictionsFormEnforces(TestCase):
    def test_cronological_dates(self):
        start = now()
        end = start - datetime.timedelta(days=30)
        post = {
            "name": "dummy",
            "description": "dummy",
            "start_datetime": start,
            "end_datetime": end,
        }
        form = forms.RestrictionsForm(post)
        self.assertFalse(form.is_valid())
