import httplib

from django.test.client import Client
from django.test import TestCase
from django.http import HttpRequest
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from oscar.apps.customer.models import CommunicationEventType
from oscar.apps.customer.history_helpers import get_recently_viewed_product_ids
from oscar.test.helpers import create_product, create_order


class HistoryHelpersTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.product = create_product()
    
    def test_viewing_product_creates_cookie(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertTrue('oscar_recently_viewed_products' in response.cookies)
        
    def test_id_gets_added_to_cookie(self):
        response = self.client.get(self.product.get_absolute_url())
        request = HttpRequest()
        request.COOKIES['oscar_recently_viewed_products'] = response.cookies['oscar_recently_viewed_products'].value
        self.assertTrue(self.product.id in get_recently_viewed_product_ids(request))


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


class AnonOrderDetail(TestCase):

    def setUp(self):
        self.client = Client()

    def test_404_received_for_unknown_order(self):
        response = self.client.get(reverse('customer:anon-order', kwargs={'order_number': 1000,
            'hash': '1231231232'}))
        self.assertEqual(httplib.NOT_FOUND, response.status_code)

    def test_200_received_for_order_with_correct_hash(self):
        order = create_order()
        response = self.client.get(reverse('customer:anon-order', kwargs={'order_number': order.number,
            'hash': order.verification_hash()}))
        self.assertEqual(httplib.OK, response.status_code)

    def test_404_received_for_order_with_incorrect_hash(self):
        order = create_order()
        response = self.client.get(reverse('customer:anon-order', kwargs={'order_number': order.number,
            'hash': 'bad'}))
        self.assertEqual(httplib.NOT_FOUND, response.status_code)


class EditProfileTests(TestCase):

    def test_change_password_page_returns_200(self):
        User.objects.create_user(username='customer',
                                 email='customer@example.com', password='')
        self.client.login(username='customer', password='')
        url = reverse('customer:profile-update')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertTrue('form' in response.context)

