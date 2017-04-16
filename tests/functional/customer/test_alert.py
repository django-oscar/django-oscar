from django_webtest import WebTest
from django.core.urlresolvers import reverse
from django.core import mail
from django.test import TestCase

from oscar.apps.customer.alerts.utils import send_product_alerts
from oscar.apps.customer.models import ProductAlert
from oscar.test.factories import create_product, create_stockrecord
from oscar.test.factories import UserFactory


class TestAUser(WebTest):

    def test_can_create_a_stock_alert(self):
        user = UserFactory()
        product = create_product(num_in_stock=0)
        product_page = self.app.get(product.get_absolute_url(), user=user)
        form = product_page.forms['alert_form']
        form.submit()

        alerts = ProductAlert.objects.filter(user=user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertEqual(ProductAlert.ACTIVE, alert.status)
        self.assertEqual(alert.product, product)


class TestAUserWithAnActiveStockAlert(WebTest):

    def setUp(self):
        self.user = UserFactory()
        self.product = create_product()
        self.stockrecord = create_stockrecord(self.product, num_in_stock=0)
        product_page = self.app.get(self.product.get_absolute_url(),
                                    user=self.user)
        form = product_page.forms['alert_form']
        form.submit()

    def test_can_cancel_it(self):
        alerts = ProductAlert.objects.filter(user=self.user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertFalse(alert.is_cancelled)
        self.app.get(
            reverse('customer:alerts-cancel-by-pk', kwargs={'pk': alert.pk}),
            user=self.user)

        alerts = ProductAlert.objects.filter(user=self.user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertTrue(alert.is_cancelled)

    def test_gets_notified_when_it_is_back_in_stock(self):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        self.assertEqual(1, self.user.notifications.all().count())

    def test_gets_emailed_when_it_is_back_in_stock(self):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        self.assertEqual(1, len(mail.outbox))

    def test_does_not_get_emailed_when_it_is_saved_but_still_zero_stock(self):
        self.stockrecord.num_in_stock = 0
        self.stockrecord.save()
        self.assertEqual(0, len(mail.outbox))


class TestAnAnonymousUser(WebTest):

    def test_can_create_a_stock_alert(self):
        product = create_product(num_in_stock=0)
        product_page = self.app.get(product.get_absolute_url())
        form = product_page.forms['alert_form']
        form['email'] = 'john@smith.com'
        form.submit()

        alerts = ProductAlert.objects.filter(email='john@smith.com')
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertEqual(ProductAlert.UNCONFIRMED, alert.status)
        self.assertEqual(alert.product, product)


class TestHurryMode(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.product = create_product()

    def test_hurry_mode_not_set_when_stock_high(self):
        # One alert, 5 items in stock. No need to hurry.
        create_stockrecord(self.product, num_in_stock=5)
        ProductAlert.objects.create(user=self.user, product=self.product)

        send_product_alerts(self.product)

        self.assertEqual(1, len(mail.outbox))
        self.assertNotIn('Beware that the amount of items in stock is limited',
            mail.outbox[0].body)

    def test_hurry_mode_set_when_stock_low(self):
        # Two alerts, 1 item in stock. Hurry mode should be set.
        create_stockrecord(self.product, num_in_stock=1)
        ProductAlert.objects.create(user=self.user, product=self.product)
        ProductAlert.objects.create(user=UserFactory(), product=self.product)

        send_product_alerts(self.product)

        self.assertEqual(2, len(mail.outbox))
        self.assertIn('Beware that the amount of items in stock is limited',
            mail.outbox[0].body)

    def test_hurry_mode_not_set_multiple_stockrecords(self):
        # Two stockrecords, 5 items in stock for one. No need to hurry.
        create_stockrecord(self.product, num_in_stock=1)
        create_stockrecord(self.product, num_in_stock=5)
        ProductAlert.objects.create(user=self.user, product=self.product)

        send_product_alerts(self.product)

        self.assertNotIn('Beware that the amount of items in stock is limited',
            mail.outbox[0].body)

    def test_hurry_mode_set_multiple_stockrecords(self):
        # Two stockrecords, low stock on both. Hurry mode should be set.
        create_stockrecord(self.product, num_in_stock=1)
        create_stockrecord(self.product, num_in_stock=1)
        ProductAlert.objects.create(user=self.user, product=self.product)
        ProductAlert.objects.create(user=UserFactory(), product=self.product)

        send_product_alerts(self.product)

        self.assertIn('Beware that the amount of items in stock is limited',
            mail.outbox[0].body)
