from django.test import TestCase
from django.core import mail

from oscar.core.compat import get_user_model
from oscar.apps.customer.utils import Dispatcher
from oscar_testsupport.factories import create_order
from oscar.apps.customer.models import CommunicationEventType


User = get_user_model()


class CommunicationTypeTest(TestCase):
    keys = ('body', 'html', 'sms', 'subject')

    def test_no_templates_returns_empty_string(self):
        et = CommunicationEventType()
        messages = et.get_messages()
        for key in self.keys:
            self.assertEqual('', messages[key])

    def test_field_template_render(self):
        et = CommunicationEventType(email_subject_template='Hello {{ name }}')
        ctx = {'name': 'world'}
        messages = et.get_messages(ctx)
        self.assertEqual('Hello world', messages['subject'])


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

        self.assertEquals(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertIn(order_number, message.body)
