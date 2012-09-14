from django.test import TestCase
from django.contrib.auth.models import User
from django_dynamic_fixture import G

from oscar.apps.notifications.models import Notification


class TestANewNotification(TestCase):

    def setUp(self):
        # Don't save models for speed
        self.notification = Notification(
            recipient=User(),
            subject="Hello")

    def test_is_in_a_users_inbox(self):
        self.assertEqual(Notification.INBOX, self.notification.location)

    def test_is_not_read(self):
        self.assertFalse(self.notification.is_read)


class TestANotification(TestCase):

    def setUp(self):
        self.notification = Notification.objects.create(
            recipient=G(User),
            subject="Hello")

    def test_can_be_archived(self):
        self.notification.archive()
        self.assertEqual(Notification.ARCHIVE, self.notification.location)
