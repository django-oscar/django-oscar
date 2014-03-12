from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.customer.models import ProductAlert
from oscar.core.compat import get_user_model
from oscar.test.factories import create_product


User = get_user_model()


class TestAnAlertForARegisteredUser(TestCase):

    def setUp(self):
        user = G(User)
        product = create_product()
        self.alert = ProductAlert.objects.create(user=user,
                                                 product=product)

    def test_defaults_to_active(self):
        self.assertTrue(self.alert.is_active)
