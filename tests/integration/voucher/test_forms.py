import datetime

import pytest
from django.utils import timezone
from django.utils.datastructures import MultiValueDict

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


@pytest.mark.django_db
def test_voucher_set_form_create():
    a_range = RangeFactory(includes_all_products=True)
    offer = ConditionalOfferFactory(
        offer_type=ConditionalOffer.VOUCHER,
        benefit=BenefitFactory(range=a_range),
        condition=ConditionFactory(range=a_range, value=1),
    )
    data = MultiValueDict(
        {
            "name": ["10% Discount"],
            "code_length": ["10"],
            "count": ["10"],
            "description": ["This is a 10% discount for mailing X"],
            "start_datetime": ["2014-10-01"],
            "end_datetime": ["2018-10-01"],
            "usage": [Voucher.MULTI_USE],
            "offers": [offer.pk],
        }
    )
    form = forms.VoucherSetForm(data)
    assert form.is_valid(), form.errors
    voucher_set = form.save()
    assert voucher_set.vouchers.count() == 10


@pytest.mark.django_db
def test_voucher_set_form_update_with_unchanged_count():
    tzinfo = timezone.get_current_timezone()
    voucher_set = VoucherSetFactory(
        name="Dummy name",
        count=5,
        code_length=12,
        description="Dummy description",
        start_datetime=datetime.datetime(2021, 2, 1, tzinfo=tzinfo),
        end_datetime=datetime.datetime(2021, 2, 28, tzinfo=tzinfo),
    )
    voucher = voucher_set.vouchers.first()
    assert voucher.usage == Voucher.MULTI_USE
    new_offers = [
        ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER),
        ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER),
    ]
    data = {
        "name": "New name",
        "code_length": 10,
        "description": "New description",
        "start_datetime": datetime.datetime(2021, 3, 1, tzinfo=tzinfo),
        "end_datetime": datetime.datetime(2021, 3, 31, tzinfo=tzinfo),
        "count": voucher_set.count,
        "usage": Voucher.SINGLE_USE,
        "offers": new_offers,
    }
    form = forms.VoucherSetForm(data, instance=voucher_set)
    assert form.is_valid(), form.errors
    voucher_set = form.save()
    assert voucher_set.vouchers.count() == 5
    for i, v in enumerate(voucher_set.vouchers.order_by("date_created")):
        assert v.name == "New name - %d" % (i + 1)
        assert len(v.code) == 14  # The code is not modified
        assert v.start_datetime == datetime.datetime(2021, 3, 1, tzinfo=tzinfo)
        assert v.end_datetime == datetime.datetime(2021, 3, 31, tzinfo=tzinfo)
        assert v.usage == Voucher.SINGLE_USE
        assert list(v.offers.all()) == new_offers


@pytest.mark.django_db
def test_voucher_set_form_update_with_changed_count():
    tzinfo = timezone.get_current_timezone()
    voucher_set = VoucherSetFactory(
        name="Dummy name",
        count=5,
        code_length=12,
        description="Dummy description",
        start_datetime=datetime.datetime(2021, 2, 1, tzinfo=tzinfo),
        end_datetime=datetime.datetime(2021, 2, 28, tzinfo=tzinfo),
    )
    voucher = voucher_set.vouchers.first()
    assert voucher.usage == Voucher.MULTI_USE
    new_offers = [
        ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER),
        ConditionalOfferFactory(offer_type=ConditionalOffer.VOUCHER),
    ]
    data = {
        "name": "New name",
        "code_length": 10,
        "description": "New description",
        "start_datetime": datetime.datetime(2021, 3, 1, tzinfo=tzinfo),
        "end_datetime": datetime.datetime(2021, 3, 31, tzinfo=tzinfo),
        "count": 10,
        "usage": Voucher.SINGLE_USE,
        "offers": new_offers,
    }
    form = forms.VoucherSetForm(data, instance=voucher_set)
    assert form.is_valid(), form.errors
    voucher_set = form.save()
    voucher_set.refresh_from_db()
    assert voucher_set.count == 10  # "count" is updated
    assert voucher_set.vouchers.count() == 10
    for i, v in enumerate(voucher_set.vouchers.order_by("date_created")):
        assert v.name == "New name - %d" % (i + 1)
        if i < 5:
            # Original vouchers
            assert len(v.code) == 14  # The code is not modified
        else:
            # New vouchers
            assert len(v.code) == 12
        assert v.start_datetime == datetime.datetime(2021, 3, 1, tzinfo=tzinfo)
        assert v.end_datetime == datetime.datetime(2021, 3, 31, tzinfo=tzinfo)
        assert v.usage == Voucher.SINGLE_USE
        assert list(v.offers.all()) == new_offers
