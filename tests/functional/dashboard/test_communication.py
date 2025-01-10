from django.core import mail
from django.urls import reverse
from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model, get_class
from oscar.test.factories import UserFactory
from oscar.test.testcases import WebTestCase, add_permissions

User = get_user_model()
CommunicationEventType = get_model("communication", "CommunicationEventType")
DashboardPermission = get_class("dashboard.permissions", "DashboardPermission")


class TestAnAdmin(WebTestCase):
    def setUp(self):
        self.staff = UserFactory(is_staff=True, username="1234")
        add_permissions(self.staff, DashboardPermission.get("communication_event_type"))
        self.commtype = CommunicationEventType.objects.create(
            name="Password reset", category=CommunicationEventType.USER_RELATED
        )

    def test_can_preview_an_email(self):
        list_page = self.app.get(reverse("dashboard:comms-list"), user=self.staff)
        update_page = list_page.click("Edit")
        form = update_page.form
        form["email_subject_template"] = "Hello {{ user.username }}"
        form["email_body_template"] = "Hello {{ user.username }}"
        form["email_body_html_template"] = "Hello {{ user.username }}"
        preview = form.submit("show_preview")
        assert "Hello 1234" in preview.content.decode("utf8")

    def test_can_send_a_preview_email(self):
        list_page = self.app.get(reverse("dashboard:comms-list"), user=self.staff)
        update_page = list_page.click("Edit")
        form = update_page.form
        form["email_subject_template"] = "Hello {{ user.username }}"
        form["email_body_template"] = "Hello {{ user.username }}"
        form["email_body_html_template"] = "Hello {{ user.username }}"
        form["preview_email"] = "testing@example.com"
        form.submit("send_preview")

        assert len(mail.outbox) == 1


class TestCommsUpdatePageWithUnicodeSlug(TestCase):
    def setUp(self):
        self.slug = "Ûul-wįth-weird-chars"
        self.commtype = CommunicationEventType.objects.create(
            name="comm-event",
            category=CommunicationEventType.USER_RELATED,
            code="Ûul-wįth-weird-chars",
        )
        self.user = User.objects.create(is_staff=True)
        add_permissions(self.user, DashboardPermission.get("communication_event_type"))
        self.client.force_login(self.user)

    def test_url_with_unicode_characters(self):
        response = self.client.get(f"/dashboard/comms/{self.slug}/")
        self.assertEqual(200, response.status_code)
