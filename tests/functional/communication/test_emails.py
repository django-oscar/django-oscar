# coding=utf-8
import os

from django.test import TestCase

from django.contrib.sites.models import Site
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile

from oscar.core.loading import get_class, get_model
from oscar.test.factories import (
    ProductAlertFactory, UserFactory, create_order, create_product)


Dispatcher = get_class('communication.utils', 'Dispatcher')
ProductImage = get_model('catalogue', 'ProductImage')


class TestConcreteEmailsSending(TestCase):

    def setUp(self):
        super(TestConcreteEmailsSending, self).setUp()
        self.user = UserFactory()
        self.dispatcher = Dispatcher()

    def _test_send_plain_text_and_html(self, outboxed_email):
        email = outboxed_email

        self.assertNotIn('</p>', email.body)  # Plain text body (because w/o </p> tags)

        html_content = email.alternatives[0][0]
        self.assertIn('</p>', html_content)

        mimetype = email.alternatives[0][1]
        self.assertEqual(mimetype, 'text/html')

    def _test_common_part(self):
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self._test_send_plain_text_and_html(mail.outbox[0])

    def test_send_registration_email_for_user(self):
        extra_context = {'user': self.user}
        self.dispatcher.send_registration_email_for_user(self.user, extra_context)

        self._test_common_part()
        self.assertEqual('Thank you for registering.', mail.outbox[0].subject)
        self.assertIn('Thank you for registering.', mail.outbox[0].body)

    def test_send_password_reset_email_for_user(self):
        extra_context = {
            'user': self.user,
            'reset_url': 'github.com/django-oscar/django-oscar',
        }
        self.dispatcher.send_password_reset_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = 'Resetting your password at {}.'.format(Site.objects.get_current())
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('Please go to the following page and choose a new password:', mail.outbox[0].body)
        self.assertIn('github.com/django-oscar/django-oscar', mail.outbox[0].body)

    def test_send_password_changed_email_for_user(self):
        extra_context = {
            'user': self.user,
            'reset_url': 'github.com/django-oscar/django-oscar',
        }
        self.dispatcher.send_password_changed_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = 'Your password changed at {}.'.format(Site.objects.get_current())
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('your password has been changed', mail.outbox[0].body)
        self.assertIn('github.com/django-oscar/django-oscar', mail.outbox[0].body)

    def test_send_email_changed_email_for_user(self):
        extra_context = {
            'user': self.user,
            'reset_url': 'github.com/django-oscar/django-oscar',
            'new_email': 'some_new@mail.com',
        }
        self.dispatcher.send_email_changed_email_for_user(self.user, extra_context)

        self._test_common_part()
        expected_subject = 'Your email address has changed at {}.'.format(Site.objects.get_current())
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('your email address has been changed', mail.outbox[0].body)
        self.assertIn('github.com/django-oscar/django-oscar', mail.outbox[0].body)
        self.assertIn('some_new@mail.com', mail.outbox[0].body)

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
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('Your order contains:', mail.outbox[0].body)
        product_title = order.lines.first().title
        self.assertIn(product_title, mail.outbox[0].body)

    def test_send_order_placed_email_with_attachments_for_user(self):
        order_number = 'SOME-NUM00042'
        order = create_order(number=order_number, user=self.user)

        extra_context = {
            'order': order,
            'lines': order.lines.all()
        }
        line = order.lines.first()
        product_image = ProductImage.objects.create(
            product=line.product,
            original=SimpleUploadedFile('fake_image.jpeg', b'file_content', content_type='image/jpeg'),
            caption='Fake Product Image',
        )
        attachments = [
            ['fake_file.html', b'file_content', 'text/html'],
            ['fake_image.png', b'file_content', 'image/png'],
            product_image.original.path,  # To test sending file from `FileField` based field
        ]
        self.dispatcher.send_order_placed_email_for_user(order, extra_context, attachments)

        # All attachments were sent with email
        self.assertEqual(len(mail.outbox[0].attachments), 3)
        self.assertListEqual(
            [attachment[0] for attachment in mail.outbox[0].attachments],
            ['fake_file.html', 'fake_image.png', 'fake_image.jpeg']
        )

        # Remove test file
        os.remove(product_image.original.path)

    def test_send_product_alert_email_for_user(self):
        product = create_product(num_in_stock=5)
        ProductAlertFactory(product=product, user=self.user)

        self.dispatcher.send_product_alert_email_for_user(product)

        self._test_common_part()
        expected_subject = u'{} is back in stock'.format(product.title)
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        self.assertIn('We are happy to inform you that our product', mail.outbox[0].body)
        # No `hurry_mode`
        self.assertNotIn('Beware that the amount of items in stock is limited.', mail.outbox[0].body)

    def test_send_product_alert_email_for_user_with_hurry_mode(self):
        another_user = UserFactory(email='another_user@mail.com')
        product = create_product(num_in_stock=1)
        ProductAlertFactory(product=product, user=self.user, email=self.user.email)
        ProductAlertFactory(product=product, user=another_user, email=another_user.email)

        self.dispatcher.send_product_alert_email_for_user(product)
        self.assertEqual(len(mail.outbox), 2)  # Separate email for each user
        expected_subject = u'{} is back in stock'.format(product.title)
        self.assertEqual(expected_subject, mail.outbox[0].subject)
        for outboxed_email in mail.outbox:
            self.assertEqual(expected_subject, outboxed_email.subject)
            self.assertIn('We are happy to inform you that our product', outboxed_email.body)
            self.assertIn('Beware that the amount of items in stock is limited.', outboxed_email.body)

    def test_send_product_alert_confirmation_email_for_user(self):
        product = create_product(num_in_stock=5)
        alert = ProductAlertFactory(product=product, user=self.user, email=self.user.email, key='key00042')

        self.dispatcher.send_product_alert_confirmation_email_for_user(alert)

        self._test_common_part()
        self.assertEqual('Confirmation required for stock alert', mail.outbox[0].subject)
        self.assertIn('Somebody (hopefully you) has requested an email alert', mail.outbox[0].body)
        self.assertIn(alert.get_confirm_url(), mail.outbox[0].body)
        self.assertIn(alert.get_cancel_url(), mail.outbox[0].body)
