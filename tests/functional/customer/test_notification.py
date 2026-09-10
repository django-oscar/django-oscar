from http import client as http_client

from django.urls import reverse

from oscar.core.loading import get_class, get_model
from oscar.test.factories import UserFactory
from oscar.test.testcases import WebTestCase

Dispatcher = get_class("communication.utils", "Dispatcher")
Notification = get_model("communication", "Notification")


class TestAUserWithUnreadNotifications(WebTestCase):
    def setUp(self):
        self.user = UserFactory()
        Dispatcher().notify_user(self.user, "Test message")

    def test_can_see_them_in_page_header(self):
        homepage = self.app.get("/", user=self.user)
        if homepage.status_code == 302:
            homepage = homepage.follow()
        self.assertEqual(1, homepage.context["num_unread_notifications"])

    def test_notification_list_view_shows_user_notifications(self):
        response = self.app.get(reverse("customer:notifications-inbox"), user=self.user)
        self.assertEqual(1, len(response.context["notifications"]))
        self.assertEqual(False, response.context["notifications"][0].is_read)

    def test_notification_marked_as_read(self):
        n = Notification.objects.first()
        path = reverse("customer:notifications-detail", kwargs={"pk": n.id})
        response = self.app.get(path, user=self.user)
        # notification should be marked as read
        self.assertEqual(http_client.OK, response.status_code)
        n.refresh_from_db()
        self.assertTrue(n.is_read)


class TestNotificationBulkActions(WebTestCase):
    csrf_checks = False

    def setUp(self):
        super().setUp()
        Dispatcher().notify_user(self.user, "Test message")
        self.notification = Notification.objects.get(recipient=self.user)

    def test_can_archive_selected_notification(self):
        response = self.post(
            reverse("customer:notifications-update"),
            params={"action": "archive", "selected_notification": self.notification.id},
        )
        self.assertEqual(http_client.FOUND, response.status_code)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.location, Notification.ARCHIVE)

    def test_can_delete_selected_notification(self):
        self.post(
            reverse("customer:notifications-update"),
            params={"action": "delete", "selected_notification": self.notification.id},
        )
        self.assertFalse(Notification.objects.filter(pk=self.notification.pk).exists())

    def test_cannot_act_on_another_users_notification(self):
        other_user = UserFactory()
        Dispatcher().notify_user(other_user, "Other message")
        other_notification = Notification.objects.get(recipient=other_user)

        self.post(
            reverse("customer:notifications-update"),
            params={
                "action": "delete",
                "selected_notification": other_notification.id,
            },
        )

        self.assertTrue(Notification.objects.filter(pk=other_notification.pk).exists())
