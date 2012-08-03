from datetime import datetime, timedelta

from django.core import mail
from django.test import TestCase
from django.core.management import call_command

from oscar.apps.catalogue.models import Product
from oscar.apps.partner.models import StockRecord, Partner
from oscar.apps.catalogue.notification.models import ProductNotification

from django_dynamic_fixture import get as G


class TestCleanNotificationsCommand(TestCase):

    def setUp(self):
        self.date_now = datetime.now()
        status_date_mapping = [
            (ProductNotification.UNCONFIRMED,
             self.date_now - timedelta(minutes=45)),
            (ProductNotification.ACTIVE,
             self.date_now),
            (ProductNotification.UNCONFIRMED,
             self.date_now - timedelta(days=1, hours=3)),
            (ProductNotification.UNCONFIRMED,
             self.date_now - timedelta(hours=7)),
            (ProductNotification.UNCONFIRMED,
             self.date_now - timedelta(days=2, hours=1)),
            (ProductNotification.INACTIVE,
             self.date_now - timedelta(days=2)),
            (ProductNotification.ACTIVE,
             self.date_now - timedelta(days=2)),
        ]

        for status, date in status_date_mapping:
            notification = G(ProductNotification, status=status)
            notification.date_created = date
            notification.save()

    def test_cleans_up_unconfirmed_notifications_with_default_settings(self):
        # Test removing all notifications that have status UNCONFIRMED and
        # are older then 24 hours which is the default
        self.assertEquals(ProductNotification.objects.count(), 7)
        call_command('oscar_cleanup_notifications', *[], **{})

        self.assertEquals(ProductNotification.objects.count(), 5)

    def test_cleans_up_unconfirmed_notifications_older_than_two_days(self):
        # Test removing all notifications that have status ``UNCONFIRMED``
        # and remove the ones older then 2 days.
        self.assertEquals(ProductNotification.objects.count(), 7)
        call_command('oscar_cleanup_notifications', *[], **{'days': '2'})

        self.assertEquals(ProductNotification.objects.count(), 6)

    def test_cleans_up_unconfirmed_notifications_older_than_6_hours(self):
        # Test removing all notifications that have status ``UNCONFIRMED``
        # and remove the ones older then 6 hours.
        self.assertEquals(ProductNotification.objects.count(), 7)
        call_command('oscar_cleanup_notifications', *[], **{'hours': '6'})

        self.assertEquals(ProductNotification.objects.count(), 4)

    def test_cleans_up_unconfirmed_notifications_older_than_1_day_2_hours(self):
        # Test removing all notifications that have status ``UNCONFIRMED``
        # and remove the ones older then 6 hours.
        self.assertEquals(ProductNotification.objects.count(), 7)
        call_command('oscar_cleanup_notifications',
                     *[], **{'days': 1, 'hours': '2'})

        self.assertEquals(ProductNotification.objects.count(), 5)


class TestSendNotificationsCommand(TestCase):

    def setUp(self):
        mail.outbox = []
        partner = Partner.objects.create(name="Partner")

        self.product1 = G(Product)
        G(StockRecord, product=self.product1, partner=partner, num_in_stock=50)

        self.product2 = G(Product)
        G(StockRecord, product=self.product2, partner=partner, num_in_stock=0)

        self.product3 = G(Product)
        G(StockRecord, product=self.product3, partner=partner, num_in_stock=1)

    def test_sends_notifications_for_products_back_in_stock(self):
        active_notif1 = G(ProductNotification, status=ProductNotification.ACTIVE,
                         product=self.product1, date_notified=None)
        active_notif2 = G(ProductNotification, status=ProductNotification.ACTIVE,
                         product=self.product1, date_notified=None)
        active_notif3 = G(ProductNotification, status=ProductNotification.ACTIVE,
                         product=self.product2, date_notified=None)
        active_notif4 = G(ProductNotification, status=ProductNotification.ACTIVE,
                         product=self.product3, date_notified=None)

        inactive_notif1 = G(ProductNotification, status=ProductNotification.INACTIVE,
                         product=self.product1, date_notified=None)
        inactive_notif2 = G(ProductNotification, status=ProductNotification.INACTIVE,
                         product=self.product2, date_notified=None)

        self.assertEquals(mail.outbox, [])

        call_command('oscar_send_notifications')

        for pk in [active_notif1.pk, active_notif2.pk, active_notif4.pk]:
            notif = ProductNotification.objects.get(pk=pk)
            self.assertEquals(notif.status, ProductNotification.INACTIVE)
            self.assertNotEqual(notif.date_notified, None)

        notif = ProductNotification.objects.get(pk=active_notif3.pk)
        self.assertEquals(notif.status, ProductNotification.ACTIVE)
        self.assertEquals(notif.date_notified, None)

        self.assertEquals(len(mail.outbox), 3)

        for pk in [inactive_notif1.pk, inactive_notif2.pk]:
            notif = ProductNotification.objects.get(pk=pk)
            self.assertEquals(notif.status, ProductNotification.INACTIVE)
            self.assertEquals(notif.date_notified, None)
