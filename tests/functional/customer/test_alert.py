import mock
import warnings

from django_webtest import WebTest

from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.core import mail
from django.test import TestCase
from oscar.utils.deprecation import RemovedInOscar20Warning

from oscar.apps.customer.alerts.utils import (
    send_alert_confirmation, send_product_alerts)
from oscar.apps.customer.forms import ProductAlertForm
from oscar.apps.customer.models import ProductAlert
from oscar.test.factories import (
    create_product, create_stockrecord, ProductAlertFactory, UserFactory)


class TestAUser(WebTest):

    def setUp(self):
        self.user = UserFactory()
        self.product = create_product(num_in_stock=0)

    def test_can_create_a_stock_alert(self):
        product_page = self.app.get(self.product.get_absolute_url(), user=self.user)
        form = product_page.forms['alert_form']
        form.submit()

        alerts = ProductAlert.objects.filter(user=self.user)
        self.assertEqual(1, len(alerts))
        alert = alerts[0]
        self.assertEqual(ProductAlert.ACTIVE, alert.status)
        self.assertEqual(alert.product, self.product)

    def test_cannot_create_multiple_alerts_for_one_product(self):
        ProductAlertFactory(user=self.user, product=self.product,
                            status=ProductAlert.ACTIVE)
        # Alert form should not allow creation of additional alerts.
        form = ProductAlertForm(user=self.user, product=self.product, data={})

        self.assertFalse(form.is_valid())
        self.assertIn(
            "You already have an active alert for this product",
            form.errors['__all__'][0])


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

    def test_can_cancel_unconfirmed_stock_alert(self):
        alert = ProductAlertFactory(
            user=None, email='john@smith.com', status=ProductAlert.UNCONFIRMED)
        self.app.get(
            reverse('customer:alerts-cancel-by-key', kwargs={'key': alert.key}))
        alert.refresh_from_db()
        self.assertTrue(alert.is_cancelled)

    def test_cannot_create_multiple_alerts_for_one_product(self):
        product = create_product(num_in_stock=0)
        alert = ProductAlertFactory(user=None, product=product,
                                    email='john@smith.com')
        alert.status = ProductAlert.ACTIVE
        alert.save()

        # Alert form should not allow creation of additional alerts.
        form = ProductAlertForm(user=AnonymousUser(), product=product,
                                data={'email': 'john@smith.com'})

        self.assertFalse(form.is_valid())
        self.assertIn(
            "There is already an active stock alert for john@smith.com",
            form.errors['__all__'][0])

    def test_cannot_create_multiple_unconfirmed_alerts(self):
        # Create an unconfirmed alert
        ProductAlertFactory(
            user=None, email='john@smith.com', status=ProductAlert.UNCONFIRMED)

        # Alert form should not allow creation of additional alerts.
        form = ProductAlertForm(
            user=AnonymousUser(),
            product=create_product(num_in_stock=0),
            data={'email': 'john@smith.com'},
        )

        self.assertFalse(form.is_valid())
        self.assertIn(
            "john@smith.com has been sent a confirmation email for another "
            "product alert on this site.", form.errors['__all__'][0])


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
        self.assertNotIn(
            'Beware that the amount of items in stock is limited',
            mail.outbox[0].body)

    def test_hurry_mode_set_when_stock_low(self):
        # Two alerts, 1 item in stock. Hurry mode should be set.
        create_stockrecord(self.product, num_in_stock=1)
        ProductAlert.objects.create(user=self.user, product=self.product)
        ProductAlert.objects.create(user=UserFactory(), product=self.product)

        send_product_alerts(self.product)

        self.assertEqual(2, len(mail.outbox))
        self.assertIn(
            'Beware that the amount of items in stock is limited',
            mail.outbox[0].body)

    def test_hurry_mode_not_set_multiple_stockrecords(self):
        # Two stockrecords, 5 items in stock for one. No need to hurry.
        create_stockrecord(self.product, num_in_stock=1)
        create_stockrecord(self.product, num_in_stock=5)
        ProductAlert.objects.create(user=self.user, product=self.product)

        send_product_alerts(self.product)

        self.assertNotIn(
            'Beware that the amount of items in stock is limited',
            mail.outbox[0].body)

    def test_hurry_mode_set_multiple_stockrecords(self):
        # Two stockrecords, low stock on both. Hurry mode should be set.
        create_stockrecord(self.product, num_in_stock=1)
        create_stockrecord(self.product, num_in_stock=1)
        ProductAlert.objects.create(user=self.user, product=self.product)
        ProductAlert.objects.create(user=UserFactory(), product=self.product)

        send_product_alerts(self.product)

        self.assertIn(
            'Beware that the amount of items in stock is limited',
            mail.outbox[0].body)


class TestAlertMessageSending(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.product = create_product()
        create_stockrecord(self.product, num_in_stock=1)

    @mock.patch('oscar.apps.customer.utils.Dispatcher.dispatch_direct_messages')
    def test_alert_confirmation_uses_dispatcher(self, mock_dispatch):
        alert = ProductAlert.objects.create(
            email='test@example.com',
            key='dummykey',
            status=ProductAlert.UNCONFIRMED,
            product=self.product
        )
        send_alert_confirmation(alert)
        self.assertEqual(mock_dispatch.call_count, 1)
        self.assertEqual(mock_dispatch.call_args[0][0], 'test@example.com')

    @mock.patch('oscar.apps.customer.utils.Dispatcher.dispatch_user_messages')
    def test_alert_uses_dispatcher(self, mock_dispatch):
        ProductAlert.objects.create(user=self.user, product=self.product)
        send_product_alerts(self.product)
        self.assertEqual(mock_dispatch.call_count, 1)
        self.assertEqual(mock_dispatch.call_args[0][0], self.user)

    def test_alert_creates_email_obj(self):
        ProductAlert.objects.create(user=self.user, product=self.product)
        send_product_alerts(self.product)
        self.assertEqual(self.user.emails.count(), 1)

    @staticmethod
    def _load_deprecated_template(path):
        from django.template.loader import select_template
        # Replace the old template paths with new ones, thereby mocking
        # the presence of the deprecated templates.
        if path.startswith('customer/alerts/emails/'):
            old_path = path.replace('customer/alerts/emails/', '')
            path_map = {
                'confirmation_body.txt': 'confirmation_body.txt',
                'confirmation_subject.txt': 'confirmation_subject.txt',
                'alert_body.txt': 'body.txt',
                'alert_subject.txt': 'subject.txt',
            }
            new_path = 'customer/emails/commtype_product_alert_{}'.format(
                path_map[old_path]
            )
            # We use 'select_template' because 'load_template' is mocked...
            return select_template([new_path])
        return select_template([path])

    @mock.patch('oscar.apps.customer.alerts.utils.loader.get_template')
    def test_deprecated_notification_templates_work(self, mock_loader):
        """
        This test can be removed when support for the deprecated templates is
        dropped.
        """
        mock_loader.side_effect = self._load_deprecated_template
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            alert = ProductAlert.objects.create(
                email='test@example.com',
                key='dummykey',
                status=ProductAlert.UNCONFIRMED,
                product=self.product
            )
            send_alert_confirmation(alert)
            # Check that warnings were raised
            self.assertTrue(
                any(item.category == RemovedInOscar20Warning for item in warning_list))
            # Check that alerts were still sent
            self.assertEqual(len(mail.outbox), 1)

    @mock.patch('oscar.apps.customer.alerts.utils.loader.get_template')
    def test_deprecated_alert_templates_work(self, mock_loader):
        """
        This test can be removed when support for the deprecated templates is
        dropped.
        """
        mock_loader.side_effect = self._load_deprecated_template
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            ProductAlert.objects.create(user=self.user, product=self.product)
            send_product_alerts(self.product)
            # Check that warnings were raised
            self.assertTrue(
                any(item.category == RemovedInOscar20Warning for item in warning_list))
            # Check that alerts were still sent
            self.assertEqual(len(mail.outbox), 1)
