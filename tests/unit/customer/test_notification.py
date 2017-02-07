from django.test import TestCase

from oscar.apps.customer.models import Notification
from oscar.apps.customer.notifications import services
from oscar.core.compat import get_user_model
from oscar.test.factories import UserFactory

User = get_user_model()


class TestANewNotification(TestCase):

    def setUp(self):
        self.notification = Notification(
            recipient=UserFactory(),
            subject="Hello")

    def test_is_in_a_users_inbox(self):
        self.assertEqual(Notification.INBOX, self.notification.location)

    def test_is_not_read(self):
        self.assertFalse(self.notification.is_read)


class TestANotification(TestCase):

    def setUp(self):
        self.notification = Notification.objects.create(
            recipient=UserFactory(),
            subject="Hello")

    def test_can_be_archived(self):
        self.notification.archive()
        self.assertEqual(Notification.ARCHIVE, self.notification.location)


class TestAServiceExistsTo(TestCase):

    def test_notify_a_single_user(self):
        user = UserFactory()
        services.notify_user(user, "Hello you!")
        self.assertEqual(1, Notification.objects.filter(
            recipient=user).count())

    def test_notify_a_set_of_users(self):
        users = [UserFactory() for i in range(3)]
        services.notify_users(User.objects.all(), "Hello everybody!")
        for user in users:
            self.assertEqual(1, Notification.objects.filter(
                recipient=user).count())
