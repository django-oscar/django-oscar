from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.apps.customer.utils import get_password_reset_url


User = get_user_model()


class CustomerUtilsTestCase(TestCase):

    def test_dispatcher_password_reset_url(self):
        user = User.objects.create_user('testuser', 'text@example.com', 'dummypassword')
        url = get_password_reset_url(user)
        self.assertTrue(url.startswith('/password-reset/confirm/'))
