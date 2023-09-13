from datetime import date, datetime
from unittest import mock

import pytz
from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from oscar.apps.customer.forms import (
    EmailUserCreationForm,
    OrderSearchForm,
    PasswordResetForm,
)
from oscar.test.factories import UserFactory


class TestEmailUserCreationForm(TestCase):
    @mock.patch("oscar.apps.customer.forms.validate_password")
    def test_validator_passed_populated_user(self, mocked_validate):
        mocked_validate.side_effect = ValidationError("That password is rubbish")

        form = EmailUserCreationForm(
            data={"email": "terry@boom.com", "password1": "terry", "password2": "terry"}
        )
        self.assertFalse(form.is_valid())

        mocked_validate.assert_called_once_with("terry", form.instance)
        self.assertEqual(mocked_validate.call_args[0][1].email, "terry@boom.com")
        self.assertEqual(form.errors["password2"], ["That password is rubbish"])


class TestPasswordResetForm(TestCase):
    def test_user_email_unicode_collision(self):
        # Regression test for CVE-2019-19844, which Oscar's PasswordResetForm
        # was vulnerable to because it had overridden the save() method.
        UserFactory(username="mike123", email="mike@example.org")
        UserFactory(username="mike456", email="mıke@example.org")
        form = PasswordResetForm({"email": "mıke@example.org"})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["mıke@example.org"])


class TestOrderSearchForm(TestCase):
    @override_settings(TIME_ZONE="Africa/Nairobi")
    def test_get_filters(self):
        form = OrderSearchForm(
            data={
                "date_from": date(2021, 1, 1),
                "date_to": date(2021, 1, 10),
                "order_number": "100",
            }
        )
        self.assertTrue(form.is_valid())

        filters = form.get_filters()
        nbi = pytz.timezone(settings.TIME_ZONE)
        self.assertEqual(
            filters,
            {
                "date_placed__gte": nbi.localize(datetime(2021, 1, 1)),
                "date_placed__lte": nbi.localize(
                    datetime(2021, 1, 10, 23, 59, 59, 999999)
                ),
                "number__contains": "100",
            },
        )
