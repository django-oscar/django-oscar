import pytest
from django.utils.datastructures import MultiValueDict

from oscar.apps.dashboard.vouchers import forms


@pytest.mark.django_db
def test_voucherform_set_create():
    data = MultiValueDict({
        'name': ['10% Discount'],
        'code_length': ['10'],
        'count': ['10'],
        'description': ['This is a 10% discount for mailing X'],
        'start_datetime': ['2014-10-01'],
        'end_datetime': ['2018-10-01'],
    })
    form = forms.VoucherSetForm(data)
    assert form.is_valid(), form.errors
    voucher_set = form.save()
    assert voucher_set.vouchers.count() == 10
