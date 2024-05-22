from datetime import timedelta

import pytest
from django import test
from django.urls import reverse
from django.utils import timezone

from oscar.apps.dashboard.vouchers import forms
from oscar.core.loading import get_model
from oscar.test.factories.offer import (
    BenefitFactory,
    ConditionalOfferFactory,
    ConditionFactory,
    RangeFactory,
)
from oscar.test.factories.voucher import VoucherSetFactory

ConditionalOffer = get_model("offer", "ConditionalOffer")
Voucher = get_model("voucher", "Voucher")


class TestVoucherForm(test.TestCase):
    def test_doesnt_crash_on_empty_date_fields(self):
        """
        There was a bug fixed in 02b3644 where the voucher form would raise an
        exception (instead of just failing validation) when being called with
        empty fields. This tests exists to prevent a regression.
        """
        offer = ConditionalOfferFactory(
            offer_type=ConditionalOffer.VOUCHER,
            benefit=BenefitFactory(range=None),
            condition=ConditionFactory(range=None, value=1),
        )
        data = {
            "code": "",
            "name": "",
            "start_datetime": "",
            "end_datetime": "",
            "usage": "Single use",
            "offers": [offer.pk],
        }
        form = forms.VoucherForm(data=data)
        try:
            form.is_valid()
        except Exception as e:
            import traceback

            self.fail(
                "Exception raised while validating voucher form: %s\n\n%s"
                % (str(e), traceback.format_exc())
            )


@pytest.mark.django_db
class TestVoucherSetForm:
    def test_valid_form(self):
        a_range = RangeFactory(includes_all_products=True)
        offer = ConditionalOfferFactory(
            offer_type=ConditionalOffer.VOUCHER,
            benefit=BenefitFactory(range=a_range),
            condition=ConditionFactory(range=a_range, value=1),
        )
        start = timezone.now()
        end = start + timedelta(days=1)
        data = {
            "name": "test",
            "code_length": 12,
            "description": "test",
            "start_datetime": start,
            "end_datetime": end,
            "count": 10,
            "usage": Voucher.MULTI_USE,
            "offers": [offer.pk],
        }
        form = forms.VoucherSetForm(data=data)
        assert form.is_valid()
        instance = form.save()
        assert instance.count == instance.vouchers.count()
        assert instance.start_datetime == start
        assert instance.end_datetime == end

    def test_valid_form_reduced_count(self):
        voucher_set = VoucherSetFactory(count=5)
        voucher = voucher_set.vouchers.first()
        data = {
            "name": voucher_set.name,
            "code_length": voucher_set.code_length,
            "description": voucher_set.description,
            "start_datetime": voucher_set.start_datetime,
            "end_datetime": voucher_set.end_datetime,
            "count": 4,
            "usage": voucher.usage,
            "offers": voucher.offers.all(),
        }
        form = forms.VoucherSetForm(data, instance=voucher_set)
        assert not form.is_valid()
        assert form.errors["count"][0] == (
            "This cannot be used to delete vouchers (currently 5) in this set. "
            'You can do that on the <a href="%s">detail</a> page.'
        ) % reverse("dashboard:voucher-set-detail", kwargs={"pk": voucher_set.pk})
