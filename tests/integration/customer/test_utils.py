from django.test import TestCase

from oscar.apps.customer.utils import get_password_reset_url, normalise_email
from oscar.core.compat import get_user_model

User = get_user_model()


class CustomerUtilsTestCase(TestCase):
    def test_dispatcher_password_reset_url(self):
        user = User.objects.create_user("testuser", "text@example.com", "dummypassword")
        url = get_password_reset_url(user)
        self.assertTrue(url.startswith("/password-reset/confirm/"))

    def test_normalise_email(self):
        self.assertEqual(
            normalise_email('"test@TEST.com"@TEST.cOm'), '"test@TEST.com"@test.com'
        )
