from django.test import TestCase
from django.core import mail

from oscar.core.compat import get_user_model
from oscar.apps.customer.utils import Dispatcher
from oscar.apps.customer.models import CommunicationEventType
from oscar.test.factories import create_order


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
                                                   category="Order related")

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
