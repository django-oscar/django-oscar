from django.core import mail
from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from oscar.test.factories import create_order

User = get_user_model()

CommunicationEventType = get_model("communication", "CommunicationEventType")
CommunicationEvent = get_model("order", "CommunicationEvent")
Email = get_model("communication", "Email")
Dispatcher = get_class("communication.utils", "Dispatcher")
OrderDispatcher = get_class("order.utils", "OrderDispatcher")


class TestDispatcher(TestCase):
    def _dispatch_order_messages(self, order_number, order, email=None):
        event_code = OrderDispatcher.ORDER_PLACED_EVENT_CODE
        et = CommunicationEventType.objects.create(
            code=event_code,
            name="Order Placed",
            category=CommunicationEventType.ORDER_RELATED,
        )

        messages = et.get_messages({"order": order, "lines": order.lines.all()})

        assert order_number in messages["body"]
        assert order_number in messages["html"]

        order_dispatcher = OrderDispatcher()
        order_dispatcher.dispatch_order_messages(order, messages, event_code)

        assert (
            CommunicationEvent.objects.filter(order=order, event_type=et).count() == 1
        )

        assert len(mail.outbox) == 1

        message = mail.outbox[0]
        assert order_number in message.body

        # Test sending messages to emails without account and text body
        messages["body"] = ""
        dispatcher = Dispatcher()
        dispatcher.dispatch_direct_messages(email, messages)
        assert len(mail.outbox) == 2

    def test_dispatch_order_messages(self):
        email = "testuser@example.com"
        user = User.objects.create_user("testuser", email, "somesimplepassword")
        order = create_order(number="12345", user=user)
        assert not order.is_anonymous
        self._dispatch_order_messages(order_number="12345", order=order, email=email)

    def test_dispatch_anonymous_order_messages(self):
        order = create_order(number="12346", guest_email="testguest@example.com")
        assert order.is_anonymous
        self._dispatch_order_messages(
            order_number="12346",
            order=order,
            email="testguest@example.com",
        )
