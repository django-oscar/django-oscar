import os

from django.core import mail
from django.test import TestCase

from oscar.core.loading import get_class
from oscar.test.factories import ProductImageFactory, create_order
from oscar.test.utils import EmailsMixin, remove_image_folders

OrderDispatcher = get_class('order.utils', 'OrderDispatcher')


class TestConcreteEmailsSending(EmailsMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.dispatcher = OrderDispatcher()

    def test_send_order_placed_email_for_user(self):
        order_number = 'SOME-NUM00042'
        order = create_order(number=order_number, user=self.user)

        extra_context = {
            'order': order,
            'lines': order.lines.all()
        }
        self.dispatcher.send_order_placed_email_for_user(order, extra_context)

        self._test_common_part()
        expected_subject = 'Confirmation of order {}'.format(order_number)
        assert expected_subject == mail.outbox[0].subject
        assert 'Your order contains:' in mail.outbox[0].body
        product_title = order.lines.first().title
        assert product_title in mail.outbox[0].body

    def test_send_order_placed_email_with_attachments_for_user(self):
        remove_image_folders()

        order_number = 'SOME-NUM00042'
        order = create_order(number=order_number, user=self.user)

        extra_context = {
            'order': order,
            'lines': order.lines.all()
        }
        line = order.lines.first()
        product_image = ProductImageFactory(product=line.product)
        attachments = [
            ['fake_file.html', b'file_content', 'text/html'],
            ['fake_image.png', b'file_content', 'image/png'],
            product_image.original.path,  # To test sending file from `FileField` based field
        ]
        self.dispatcher.send_order_placed_email_for_user(order, extra_context, attachments)

        # All attachments were sent with email
        assert len(mail.outbox[0].attachments) == 3
        expected_attachments = ['fake_file.html', 'fake_image.png', 'test_image.jpg']
        assert [attachment[0] for attachment in mail.outbox[0].attachments] == expected_attachments

        # Remove test file
        os.remove(product_image.original.path)
