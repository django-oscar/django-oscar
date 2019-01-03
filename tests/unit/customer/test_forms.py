from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase

from oscar.apps.customer.forms import EmailUserCreationForm


class TestEmailUserCreationForm(TestCase):

    @mock.patch('oscar.apps.customer.forms.validate_password')
    def test_validator_passed_populated_user(self, mocked_validate):
        mocked_validate.side_effect = ValidationError('That password is rubbish')

        form = EmailUserCreationForm(data={'email': 'terry@boom.com', 'password1': 'terry', 'password2': 'terry'})
        self.assertFalse(form.is_valid())

        mocked_validate.assert_called_once_with('terry', form.instance)
        self.assertEqual(mocked_validate.call_args[0][1].email, 'terry@boom.com')
        self.assertEqual(form.errors['password2'], ['That password is rubbish'])
