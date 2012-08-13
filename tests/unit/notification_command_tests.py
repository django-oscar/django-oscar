from datetime import datetime, timedelta
from django.test import TestCase
from django.core.management import call_command

from django_dynamic_fixture import get

from oscar.apps.catalogue.notification.models import ProductNotification


class CleanNotificationsTests(TestCase):

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
            notification = get(ProductNotification, status=status)
            notification.date_created = date
            notification.save()

    def test_cleanup_unconfirmed_notifications_defaults(self):
        """
        Test removing all notifications that have status UNCONFIRMED and
        are older then 24 hours which is the default
        """
        self.assertEquals(ProductNotification.objects.count(), 7)
        call_command('oscar_cleanup_notifications', *[], **{})

        self.assertEquals(ProductNotification.objects.count(), 5)

    def test_cleanup_unconfirmed_notifications_two_days(self):
        """
        Test removing all notifications that have status ``UNCONFIRMED``
        and remove the ones older then 2 days.
        """
        self.assertEquals(ProductNotification.objects.count(), 7)
        call_command('oscar_cleanup_notifications', *[], **{'days': '2'})

        self.assertEquals(ProductNotification.objects.count(), 6)

    def test_cleanup_unconfirmed_notifications_6_hours(self):
        """
        Test removing all notifications that have status ``UNCONFIRMED``
        and remove the ones older then 6 hours.
        """
        self.assertEquals(ProductNotification.objects.count(), 7)
        call_command('oscar_cleanup_notifications', *[], **{'hours': '6'})

        self.assertEquals(ProductNotification.objects.count(), 4)

    def test_cleanup_unconfirmed_notifications_1_day_2_hours(self):
        """
        Test removing all notifications that have status ``UNCONFIRMED``
        and remove the ones older then 6 hours.
        """
        self.assertEquals(ProductNotification.objects.count(), 7)
        call_command('oscar_cleanup_notifications',
                     *[], **{'days': 1, 'hours': '2'})

        self.assertEquals(ProductNotification.objects.count(), 5)
