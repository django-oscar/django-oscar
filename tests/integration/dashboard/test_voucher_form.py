from datetime import timedelta

import pytest
from django import test
from django.utils import timezone

from oscar.apps.dashboard.vouchers import forms
from oscar.test.factories.offer import RangeFactory


class TestVoucherForm(test.TestCase):

    def test_doesnt_crash_on_empty_date_fields(self):
        """
        There was a bug fixed in 02b3644 where the voucher form would raise an
        exception (instead of just failing validation) when being called with
        empty fields. This tests exists to prevent a regression.
        """
        data = {
            'code': '',
            'name': '',
            'start_date': '',
            'end_date': '',
            'benefit_range': '',
            'benefit_type': 'Percentage',
            'usage': 'Single use',
        }
        form = forms.VoucherForm(data=data)
        try:
            form.is_valid()
        except Exception as e:
            import traceback
            self.fail(
                "Exception raised while validating voucher form: %s\n\n%s" % (
                    e.message, traceback.format_exc()))


@pytest.mark.django_db
class TestVoucherSetForm:

    def test_valid_form(self):
        a_range = RangeFactory(includes_all_products=True)

        start = timezone.now()
        end = start + timedelta(days=1)
        data = {
            'name': 'test',
            'code_length': 12,
            'description': 'test',
            'start_datetime': start,
            'end_datetime': end,
            'count': 10,
            'benefit_range': a_range.pk,
            'benefit_type': 'Percentage',
            'benefit_value': 10,
        }
        form = forms.VoucherSetForm(data=data)
        assert form.is_valid()
        instance = form.save()
        assert instance.count == instance.vouchers.count()
        assert instance.start_datetime == start
        assert instance.end_datetime == end
