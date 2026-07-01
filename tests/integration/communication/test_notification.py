from django.test import TestCase

from oscar.apps.communication.models import Notification
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class
from oscar.test.factories import UserFactory

User = get_user_model()

Dispatcher = get_class("communication.utils", "Dispatcher")


class TestANewNotification(TestCase):
    def setUp(self):
        self.notification = Notification(recipient=UserFactory(), subject="Hello")

    def test_is_in_a_users_inbox(self):
        assert Notification.INBOX == self.notification.location

    def test_is_not_read(self):
        assert not self.notification.is_read


class TestANotification(TestCase):
    def setUp(self):
        self.notification = Notification.objects.create(
            recipient=UserFactory(), subject="Hello"
        )

    def test_can_be_archived(self):
        self.notification.archive()
        assert Notification.ARCHIVE == self.notification.location


class NotificationServiceTestCase(TestCase):
    def test_notify_a_single_user(self):
        user = UserFactory()
        subj = "Hello you!"
        body = "This is the notification body."

        Dispatcher().notify_user(user, subj, body=body)
        user_notification = Notification.objects.get(recipient=user)
        assert user_notification.subject == subj
        assert user_notification.body == body

    def test_notify_a_set_of_users(self):
        users = UserFactory.create_batch(3)
        subj = "Hello everyone!"
        body = "This is the notification body."

        Dispatcher().notify_users(User.objects.all(), subj, body=body)
        for user in users:
            user_notification = Notification.objects.get(recipient=user)
            assert user_notification.subject == subj
            assert user_notification.body == body
