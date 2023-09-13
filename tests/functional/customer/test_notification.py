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
