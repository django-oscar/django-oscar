from django.test.client import Client
from django.test import TestCase
from django.http import HttpRequest

from oscar.apps.customer.models import CommunicationEventType
from oscar.apps.customer.history_helpers import get_recently_viewed_product_ids
from oscar.test.helpers import create_product

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

