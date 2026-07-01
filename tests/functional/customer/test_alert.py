from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django_webtest import WebTest

from oscar.apps.customer.forms import ProductAlertForm
from oscar.apps.customer.models import ProductAlert
from oscar.core.loading import get_class
from oscar.test.factories import (
    ProductAlertFactory,
    UserFactory,
    create_product,
    create_stockrecord,
)

CustomerDispatcher = get_class("customer.utils", "CustomerDispatcher")
AlertsDispatcher = get_class("customer.alerts.utils", "AlertsDispatcher")


class TestProductAlert(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.product = create_product(num_in_stock=0)

    def test_can_create_a_stock_alert(self):
        product_page = self.app.get(self.product.get_absolute_url(), user=self.user)
        form = product_page.forms["alert_form"]
        form.submit()

        alerts = ProductAlert.objects.filter(user=self.user)
        assert len(alerts) == 1
        alert = alerts[0]
        assert ProductAlert.ACTIVE == alert.status
        assert alert.product == self.product

    def test_cannot_create_multiple_alerts_for_one_product(self):
        ProductAlertFactory(
            user=self.user, product=self.product, status=ProductAlert.ACTIVE
        )
        # Alert form should not allow creation of additional alerts.
        form = ProductAlertForm(user=self.user, product=self.product, data={})

        assert not form.is_valid()
        assert (
            "You already have an active alert for this product"
            in form.errors["__all__"][0]
        )


class TestAUserWithAnActiveStockAlert(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.product = create_product()
        self.stockrecord = create_stockrecord(self.product, num_in_stock=0)
        product_page = self.app.get(self.product.get_absolute_url(), user=self.user)
        form = product_page.forms["alert_form"]
        form.submit()

    def test_can_cancel_it(self):
        alerts = ProductAlert.objects.filter(user=self.user)
        assert len(alerts) == 1
        alert = alerts[0]
        assert not alert.is_cancelled
        self.app.get(
            reverse("customer:alerts-cancel-by-pk", kwargs={"pk": alert.pk}),
            user=self.user,
        )

        alerts = ProductAlert.objects.filter(user=self.user)
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.is_cancelled

    def test_gets_notified_when_it_is_back_in_stock(self):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        assert self.user.notifications.all().count() == 1

    def test_gets_emailed_when_it_is_back_in_stock(self):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        assert len(mail.outbox) == 1

    def test_does_not_get_emailed_when_it_is_saved_but_still_zero_stock(self):
        self.stockrecord.num_in_stock = 0
        self.stockrecord.save()
        assert len(mail.outbox) == 0

    @mock.patch("oscar.apps.communication.utils.Dispatcher.notify_user")
    def test_site_notification_sent(self, mock_notify):
        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()
        mock_notify.assert_called_once_with(
            self.user,
            "{} is back in stock".format(self.product.title),
            body='<a href="{}">{}</a> is back in stock'.format(
                self.product.get_absolute_url(), self.product.title
            ),
        )

    @mock.patch("oscar.apps.communication.utils.Dispatcher.notify_user")
    def test_product_title_truncated_in_alert_notification_subject(self, mock_notify):
        self.product.title = (
            "Aut nihil dignissimos perspiciatis. Beatae sed consequatur odit incidunt. "
            "Quaerat labore perferendis quasi aut sunt maxime accusamus laborum. "
            "Ut quam repudiandae occaecati eligendi. Nihil rem vel eos."
        )
        self.product.save()

        self.stockrecord.num_in_stock = 10
        self.stockrecord.save()

        mock_notify.assert_called_once_with(
            self.user,
            "{} is back in stock".format(self.product.title[:200]),
            body='<a href="{}">{}</a> is back in stock'.format(
                self.product.get_absolute_url(), self.product.title
            ),
        )


class TestAnAnonymousUser(WebTest):
    def test_can_create_a_stock_alert(self):
        product = create_product(num_in_stock=0)
        product_page = self.app.get(product.get_absolute_url())
        form = product_page.forms["alert_form"]
        form["email"] = "john@smith.com"
        form.submit()

        alerts = ProductAlert.objects.filter(email="john@smith.com")
        assert len(alerts) == 1
        alert = alerts[0]
        assert ProductAlert.UNCONFIRMED == alert.status
        assert alert.product == product

    def test_can_cancel_unconfirmed_stock_alert(self):
        alert = ProductAlertFactory(
            user=None, email="john@smith.com", status=ProductAlert.UNCONFIRMED
        )
        self.app.get(
            reverse("customer:alerts-cancel-by-key", kwargs={"key": alert.key})
        )
        alert.refresh_from_db()
        assert alert.is_cancelled

    def test_cannot_create_multiple_alerts_for_one_product(self):
        product = create_product(num_in_stock=0)
        alert = ProductAlertFactory(user=None, product=product, email="john@smith.com")
        alert.status = ProductAlert.ACTIVE
        alert.save()

        # Alert form should not allow creation of additional alerts.
        form = ProductAlertForm(
            user=AnonymousUser(), product=product, data={"email": "john@smith.com"}
        )

        assert not form.is_valid()
        assert (
            "There is already an active stock alert for john@smith.com"
            in form.errors["__all__"][0]
        )

    def test_cannot_create_multiple_unconfirmed_alerts(self):
        # Create an unconfirmed alert
        ProductAlertFactory(
            user=None, email="john@smith.com", status=ProductAlert.UNCONFIRMED
        )

        # Alert form should not allow creation of additional alerts.
        form = ProductAlertForm(
            user=AnonymousUser(),
            product=create_product(num_in_stock=0),
            data={"email": "john@smith.com"},
        )

        assert not form.is_valid()
        message = "john@smith.com has been sent a confirmation email for another product alert on this site."
        assert message in form.errors["__all__"][0]


class TestHurryMode(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.product = create_product()
        self.dispatcher = AlertsDispatcher()

    def test_hurry_mode_not_set_when_stock_high(self):
        # One alert, 5 items in stock. No need to hurry.
        create_stockrecord(self.product, num_in_stock=5)
        ProductAlert.objects.create(user=self.user, product=self.product)

        self.dispatcher.send_product_alert_email_for_user(self.product)

        assert len(mail.outbox) == 1
        assert (
            "Beware that the amount of items in stock is limited"
            not in mail.outbox[0].body
        )

    def test_hurry_mode_set_when_stock_low(self):
        # Two alerts, 1 item in stock. Hurry mode should be set.
        create_stockrecord(self.product, num_in_stock=1)
        ProductAlert.objects.create(user=self.user, product=self.product)
        ProductAlert.objects.create(user=UserFactory(), product=self.product)

        self.dispatcher.send_product_alert_email_for_user(self.product)

        assert len(mail.outbox) == 2
        assert (
            "Beware that the amount of items in stock is limited" in mail.outbox[0].body
        )

    def test_hurry_mode_not_set_multiple_stockrecords(self):
        # Two stockrecords, 5 items in stock for one. No need to hurry.
        create_stockrecord(self.product, num_in_stock=1)
        create_stockrecord(self.product, num_in_stock=5)
        ProductAlert.objects.create(user=self.user, product=self.product)

        self.dispatcher.send_product_alert_email_for_user(self.product)

        assert (
            "Beware that the amount of items in stock is limited"
            not in mail.outbox[0].body
        )

    def test_hurry_mode_set_multiple_stockrecords(self):
        # Two stockrecords, low stock on both. Hurry mode should be set.
        create_stockrecord(self.product, num_in_stock=1)
        create_stockrecord(self.product, num_in_stock=1)
        ProductAlert.objects.create(user=self.user, product=self.product)
        ProductAlert.objects.create(user=UserFactory(), product=self.product)

        self.dispatcher.send_product_alert_email_for_user(self.product)

        assert (
            "Beware that the amount of items in stock is limited" in mail.outbox[0].body
        )


class TestAlertMessageSending(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.product = create_product()
        create_stockrecord(self.product, num_in_stock=1)
        self.dispatcher = AlertsDispatcher()

    @mock.patch("oscar.apps.communication.utils.Dispatcher.dispatch_direct_messages")
    def test_alert_confirmation_uses_dispatcher(self, mock_dispatch):
        alert = ProductAlert.objects.create(
            email="test@example.com",
            key="dummykey",
            status=ProductAlert.UNCONFIRMED,
            product=self.product,
        )
        AlertsDispatcher().send_product_alert_confirmation_email_for_user(alert)
        assert mock_dispatch.call_count == 1
        assert mock_dispatch.call_args[0][0] == "test@example.com"

    @mock.patch("oscar.apps.communication.utils.Dispatcher.dispatch_user_messages")
    def test_alert_uses_dispatcher(self, mock_dispatch):
        ProductAlert.objects.create(user=self.user, product=self.product)
        self.dispatcher.send_product_alert_email_for_user(self.product)
        assert mock_dispatch.call_count == 1
        assert mock_dispatch.call_args[0][0] == self.user

    def test_alert_creates_email_obj(self):
        ProductAlert.objects.create(user=self.user, product=self.product)
        self.dispatcher.send_product_alert_email_for_user(self.product)
        assert self.user.emails.count() == 1
