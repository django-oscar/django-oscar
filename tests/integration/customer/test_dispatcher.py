from django.test import TestCase
from django.core import mail

from oscar.core.compat import get_user_model
from oscar.apps.customer.utils import Dispatcher, get_password_reset_url
from oscar.apps.customer.models import CommunicationEventType, Email
from oscar.test.factories import create_order, SiteFactory


User = get_user_model()


class TestDispatcher(TestCase):

    def test_sending_a_order_related_messages(self):
        email = 'testuser@example.com'
        user = User.objects.create_user('testuser', email,
                                        'somesimplepassword')

        order_number = '12345'
        order = create_order(number=order_number, user=user)
        et = CommunicationEventType.objects.create(code="ORDER_PLACED",
                                                   name="Order Placed",
                                                   category=CommunicationEventType.ORDER_RELATED)

        messages = et.get_messages({
            'order': order,
            'lines': order.lines.all()
        })

        self.assertIn(order_number, messages['body'])
        self.assertIn(order_number, messages['html'])

        dispatcher = Dispatcher()
        dispatcher.dispatch_order_messages(order, messages, et)

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertIn(order_number, message.body)

        # test sending messages to emails without account and text body
        messages['body'] = ''
        dispatcher.dispatch_direct_messages(email, messages)
        self.assertEqual(len(mail.outbox), 2)

    def test_sending_user_related_message(self):
        email = 'testuser@example.com'
        user = User.objects.create_user('testuser', email,
                                        'somesimplepassword')
        CommunicationEventType.objects.create(code='EMAIL_CHANGED',
                                              name='Email Changed',
                                              category=CommunicationEventType.USER_RELATED)
        ctx = {
            'user': user,
            'site': SiteFactory(name='Test Site'),
            'reset_url': get_password_reset_url(user),
            'new_email': 'newtestuser@example.com',
        }
        msgs = CommunicationEventType.objects.get_and_render(
            code='EMAIL_CHANGED', context=ctx)
        Dispatcher().dispatch_user_messages(user, msgs)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, 'Your email address has changed at Test Site.')
        self.assertEquals(Email.objects.count(), 1)
        email = Email.objects.last()
        self.assertEquals(email.user.id, user.id)
        self.assertEquals(email.email, 'testuser@example.com')
