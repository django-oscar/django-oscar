from django import test

from oscar.apps.dashboard.vouchers import forms


class TestVoucherForm(test.TestCase):

    def test_handles_empty_date_fields(self):
        data = {'code': '',
                'name': '',
                'start_date': '',
                'end_date': '',
                'benefit_range': '',
                'benefit_type': 'Percentage',
                'usage': 'Single use'}
        form = forms.VoucherForm(data=data)
        try:
            form.is_valid()
        except Exception as e:
            import traceback
            self.fail("Validating form failed: %s\n\n%s" % (
                e.message, traceback.format_exc()))
