import datetime

from django.core.exceptions import ImproperlyConfigured
from django.forms import ValidationError
from django.test import TestCase
from freezegun import freeze_time

from oscar.apps.payment import forms, models

# types=[bankcards.VISA, bankcards.VISA_ELECTRON, bankcards.MASTERCARD,
#               bankcards.AMEX, bankcards.MAESTRO, bankcards.DINERS_CLUB,
#               bankcards.DISCOVER, bankcards.JCB, bankcards.CHINA_UNIONPAY,
#               bankcards.SOLO, bankcards.LASER, bankcards.SWITCH]


class TestBankcardNumberField(TestCase):
    def setUp(self):
        self.field = forms.BankcardNumberField()

    def test_strips_non_digits(self):
        self.assertEqual("4111111111111111", self.field.clean("  4111 1111 1111 1111"))

    def test_rejects_numbers_which_dont_pass_luhn(self):
        with self.assertRaises(ValidationError):
            self.field.clean("1234123412341234")

    def test_amex_accepted_when_allowed(self):
        # Number taken from http://www.darkcoding.net/credit-card-numbers/
        self.field = forms.BankcardNumberField(types=["American Express"])
        self.assertEqual("348934265521923", self.field.clean("348934265521923"))

    def test_amex_rejected_when_disallowed(self):
        self.field = forms.BankcardNumberField(types=["Visa"])
        with self.assertRaises(ValidationError):
            self.field.clean("348934265521923")

    def test_raises_error_for_invalid_card_type(self):
        with self.assertRaises(ImproperlyConfigured):
            self.field = forms.BankcardNumberField(
                types=["American Express", "Nonsense"]
            )

    def test_rejects_none(self):
        with self.assertRaises(ValidationError):
            self.field.clean(None)


@freeze_time("2016-01-01")  # BankcardStartingMonthField limits date to last 5 years
class TestStartingMonthField(TestCase):
    def setUp(self):
        self.field = forms.BankcardStartingMonthField()

    def test_returns_a_date(self):
        start_date = self.field.clean(["01", "2014"])
        self.assertTrue(isinstance(start_date, datetime.date))

    def test_rejects_invalid_months(self):
        with self.assertRaises(ValidationError):
            self.field.clean(["00", "2014"])

    def test_rejects_invalid_years(self):
        with self.assertRaises(ValidationError):
            self.field.clean(["01", "201"])

    def test_rejects_months_in_the_future(self):
        today = datetime.date.today()
        with self.assertRaises(ValidationError):
            self.field.clean(["01", today.year + 1])

    def test_returns_the_first_day_of_month(self):
        start_date = self.field.clean(["01", "2014"])
        self.assertEqual(1, start_date.day)


class TestExpiryMonthField(TestCase):
    def setUp(self):
        self.field = forms.BankcardExpiryMonthField()

    def test_returns_a_date(self):
        today = datetime.date.today()
        end_date = self.field.clean(["01", today.year + 1])
        self.assertTrue(isinstance(end_date, datetime.date))

    def test_rejects_invalid_months(self):
        with self.assertRaises(ValidationError):
            self.field.clean(["00", "2014"])

    def test_rejects_invalid_years(self):
        with self.assertRaises(ValidationError):
            self.field.clean(["01", "201"])

    def test_rejects_months_in_the_past(self):
        today = datetime.date.today()
        with self.assertRaises(ValidationError):
            self.field.clean(["01", today.year - 1])

    def test_returns_last_day_of_month(self):
        today = datetime.date.today()
        end_date = self.field.clean(["01", today.year + 1])
        self.assertEqual(31, end_date.day)

    def test_defaults_to_current_month(self):
        today = datetime.date.today()
        self.assertEqual(["%.2d" % today.month, today.year], self.field.initial)


class TestOptionalExpiryMonthField(TestExpiryMonthField):
    def setUp(self):
        self.field = forms.BankcardExpiryMonthField(required=False)

    def test_accepts_none(self):
        self.field.clean(None)


class TestCCVField(TestCase):
    """CCV field"""

    def setUp(self):
        self.field = forms.BankcardCCVField()

    def test_is_required_by_default(self):
        with self.assertRaises(ValidationError):
            self.field.clean("")

    def test_only_permits_3_or_4_digit_numbers(self):
        invalid = ["00", "12a", "12345"]
        for sample in invalid:
            with self.assertRaises(ValidationError):
                self.field.clean(sample)
        valid = ["123", "  123   ", "1235"]
        for sample in valid:
            self.field.clean(sample)

    def test_has_meaningful_error_message(self):
        try:
            self.field.clean("asdf")
        except ValidationError as e:
            self.assertEqual("Please enter a 3 or 4 digit number", e.messages[0])


class TestValidBankcardForm(TestCase):
    def setUp(self):
        today = datetime.date.today()
        data = {
            "number": "1000010000000007",
            "ccv": "123",
            "expiry_month_0": "01",
            "expiry_month_1": today.year + 1,
        }
        self.form = forms.BankcardForm(data)
        self.assertTrue(self.form.is_valid())

    def test_has_bankcard_property(self):
        self.assertTrue(isinstance(self.form.bankcard, models.Bankcard))

    def test_returns_bankcard_with_sensitive_data_intact(self):
        bankcard = self.form.bankcard
        self.assertFalse(bankcard.number.startswith("X"))
        self.assertEqual("123", bankcard.ccv)


class TestBankcardForm(TestCase):
    def test_requires_4_digit_ccv_for_amex(self):
        today = datetime.date.today()
        data = {
            "number": "378282246310005",
            "ccv": "123",
            "expiry_month_0": "01",
            "expiry_month_1": today.year + 1,
        }
        form = forms.BankcardForm(data)
        self.assertFalse(form.is_valid())
