from django.test import TestCase

from oscar.apps.customer.models import ProductAlert
from oscar.core.compat import get_user_model
from oscar.test import factories


User = get_user_model()


class TestAnAlertForARegisteredUser(TestCase):

    def setUp(self):
        user = factories.UserFactory()
        product = factories.StandaloneProductFactory()
        self.alert = ProductAlert.objects.create(user=user,
                                                 product=product)

    def test_defaults_to_active(self):
        self.assertTrue(self.alert.is_active)
