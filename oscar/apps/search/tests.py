from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from django.core import management
from haystack import backend


class SuggestViewTest(TestCase):
    fixtures = ['sample-products']

    def setUp(self):
        #clear out existing index without prompting user and ensure that
        #fixtures are indexed
        self.client = Client()
        sb = backend.SearchBackend()
        sb.clear()
        management.call_command('update_index', verbosity=0) #silenced

    def test_term_in_fixtures_found(self):
        url = reverse('oscar-search-suggest')
        response = self.client.get(url, {'query_term': 'Pint'})
        self.assertEquals(200, response.status_code)
        self.assertTrue('Pint' in response.content) #ensuring we actually find a result in the response

class MultiFacetedSearchViewTest(TestCase):
    fixtures = ['sample-products']

    def setUp(self):
        #clear out existing index without prompting user and ensure that
        #fixtures are indexed
        self.client = Client()
        sb = backend.SearchBackend()
        sb.clear()
        management.call_command('update_index', verbosity=0) #silenced

    def test_with_query(self):
        url = reverse('oscar-search')
        response = self.client.get(url, {'q': 'Pint'})
        self.assertEquals(200, response.status_code)
        self.assertTrue('value="Pint"' in response.content) #ensuring query field is set
    
        
