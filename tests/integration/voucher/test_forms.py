import pytest
from django.utils.datastructures import MultiValueDict

from oscar.apps.dashboard.vouchers import forms
from oscar.test.factories.offer import RangeFactory


@pytest.mark.django_db
def test_voucherform_set_create():
    a_range = RangeFactory(
        includes_all_products=True
    )
    data = MultiValueDict({
        'name': ['10% Discount'],
        'code_length': ['10'],
        'count': ['10'],
        'description': ['This is a 10% discount for mailing X'],
        'start_datetime': ['2014-10-01'],
        'end_datetime': ['2018-10-01'],
        'benefit_range': [a_range.pk],
        'benefit_type': ['Percentage'],
        'benefit_value': ['10'],
    })
    form = forms.VoucherSetForm(data)
    assert form.is_valid(), form.errors
    voucher_set = form.save()
    assert voucher_set.vouchers.count() == 10
