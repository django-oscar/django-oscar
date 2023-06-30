from django.core import mail
from django.test import TestCase

from oscar.apps.customer.utils import get_password_reset_url
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from oscar.test.factories import SiteFactory

User = get_user_model()

CommunicationEventType = get_model("communication", "CommunicationEventType")
Email = get_model("communication", "Email")
Dispatcher = get_class("communication.utils", "Dispatcher")
CustomerDispatcher = get_class("customer.utils", "CustomerDispatcher")


class TestDispatcher(TestCase):
    def _dispatch_user_messages(self, user, event_code, ctx, subject):
        msgs = CommunicationEventType.objects.get_and_render(
            code=event_code, context=ctx
        )
        Dispatcher().dispatch_user_messages(user, msgs)
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == subject
        assert Email.objects.count() == 1
        email = Email.objects.last()
        assert email.user.id == user.id
        assert email.email == "testuser@example.com"

    def test_dispatch_email_changed_user_message(self):
        user = User.objects.create_user(
            "testuser", "testuser@example.com", "somesimplepassword"
        )
        event_code = CustomerDispatcher.EMAIL_CHANGED_EVENT_CODE
        CommunicationEventType.objects.create(
            code=event_code,
            name="Email Changed",
            category=CommunicationEventType.USER_RELATED,
        )
        ctx = {
            "user": user,
            "site": SiteFactory(name="Test Site"),
            "reset_url": get_password_reset_url(user),
            "new_email": "newtestuser@example.com",
        }
        self._dispatch_user_messages(
            user, event_code, ctx, "Your email address has changed at Test Site."
        )

    def test_dispatch_registration_email_message(self):
        user = User.objects.create_user(
            "testuser", "testuser@example.com", "somesimplepassword"
        )
        event_code = CustomerDispatcher.REGISTRATION_EVENT_CODE
        CommunicationEventType.objects.create(
            code=event_code,
            name="Registration",
            category=CommunicationEventType.USER_RELATED,
        )
        ctx = {"user": user, "site": SiteFactory()}
        self._dispatch_user_messages(
            user, event_code, ctx, "Thank you for registering."
        )

    def test_dispatcher_uses_email_connection(self):
        connection = mail.get_connection()
        disp = Dispatcher(mail_connection=connection)
        disp.dispatch_direct_messages(
            "test@example.com",
            {
                "subject": "Test",
                "body": "This is a test.",
                "html": "",
            },
        )
        assert len(mail.outbox) == 1
