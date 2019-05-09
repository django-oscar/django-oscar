from django.core import mail
from django.test import TestCase

from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model
from oscar.apps.customer.utils import get_password_reset_url
from oscar.test.factories import create_order, SiteFactory

User = get_user_model()

CommunicationEventType = get_model('communication', 'CommunicationEventType')
CommunicationEvent = get_model('order', 'CommunicationEvent')
Email = get_model('communication', 'Email')
Dispatcher = get_class('communication.utils', 'Dispatcher')
OrderDispatcher = get_class('order.utils', 'OrderDispatcher')
CustomerDispatcher = get_class('customer.utils', 'CustomerDispatcher')


class TestDispatcher(TestCase):

    def _dispatch_order_messages(self, order_number, order, email=None):
        event_code = OrderDispatcher.ORDER_PLACED_EVENT_CODE
        et = CommunicationEventType.objects.create(
            code=event_code,
            name="Order Placed",
            category=CommunicationEventType.ORDER_RELATED,
        )

        messages = et.get_messages({
            'order': order,
            'lines': order.lines.all()
        })

        assert order_number in messages['body']
        assert order_number in messages['html']

        dispatcher = Dispatcher()
        dispatcher.dispatch_order_messages(order, messages, event_code)

        assert CommunicationEvent.objects.filter(order=order, event_type=et).count() == 1

        assert len(mail.outbox) == 1

        message = mail.outbox[0]
        assert order_number in message.body

        # Test sending messages to emails without account and text body
        messages['body'] = ''
        dispatcher.dispatch_direct_messages(email, messages)
        assert len(mail.outbox) == 2

    def _dispatch_user_messages(self, user, event_code, ctx, subject):
        msgs = CommunicationEventType.objects.get_and_render(code=event_code, context=ctx)
        Dispatcher().dispatch_user_messages(user, msgs)
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == subject
        assert Email.objects.count() == 1
        email = Email.objects.last()
        assert email.user.id == user.id
        assert email.email == 'testuser@example.com'

    def test_dispatch_order_messages(self):
        email = 'testuser@example.com'
        user = User.objects.create_user('testuser', email, 'somesimplepassword')
        order = create_order(number='12345', user=user)
        assert not order.is_anonymous
        self._dispatch_order_messages(order_number='12345', order=order, email=email)

    def test_dispatch_anonymous_order_messages(self):
        order = create_order(number='12346', guest_email='testguest@example.com')
        assert order.is_anonymous
        self._dispatch_order_messages(order_number='12346', order=order, email='testguest@example.com', )

    def test_dispatch_email_changed_user_message(self):
        user = User.objects.create_user('testuser', 'testuser@example.com', 'somesimplepassword')
        event_code = CustomerDispatcher.EMAIL_CHANGED_EVENT_CODE
        CommunicationEventType.objects.create(
            code=event_code,
            name='Email Changed',
            category=CommunicationEventType.USER_RELATED,
        )
        ctx = {
            'user': user,
            'site': SiteFactory(name='Test Site'),
            'reset_url': get_password_reset_url(user),
            'new_email': 'newtestuser@example.com',
        }
        self._dispatch_user_messages(
            user, event_code, ctx, 'Your email address has changed at Test Site.'
        )

    def test_dispatch_registration_email_message(self):
        user = User.objects.create_user('testuser', 'testuser@example.com', 'somesimplepassword')
        event_code = CustomerDispatcher.REGISTRATION_EVENT_CODE
        CommunicationEventType.objects.create(
            code=event_code,
            name='Registration',
            category=CommunicationEventType.USER_RELATED,
        )
        ctx = {'user': user,
               'site': SiteFactory()}
        self._dispatch_user_messages(user, event_code, ctx, 'Thank you for registering.')

    def test_dispatcher_uses_email_connection(self):
        connection = mail.get_connection()
        disp = Dispatcher(mail_connection=connection)
        disp.dispatch_direct_messages('test@example.com', {
            'subject': 'Test',
            'body': 'This is a test.',
            'html': '',
        })
        assert len(mail.outbox) == 1
