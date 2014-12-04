from django import test

from oscar.apps.dashboard.vouchers import forms


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
