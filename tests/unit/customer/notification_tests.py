from django.test import TestCase
from django_dynamic_fixture import G

from oscar.apps.customer.models import Notification
from oscar.apps.customer.notifications import services
from oscar.core.compat import get_user_model


User = get_user_model()


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


class TestAServiceExistsTo(TestCase):

    def test_notify_a_single_user(self):
        user = G(User)
        services.notify_user(user, "Hello you!")
        self.assertEqual(1, Notification.objects.filter(
            recipient=user).count())

    def test_notify_a_set_of_users(self):
        users = [G(User) for i in range(5)]
        services.notify_users(User.objects.all(), "Hello everybody!")
        for user in users:
            self.assertEqual(1, Notification.objects.filter(
                recipient=user).count())
