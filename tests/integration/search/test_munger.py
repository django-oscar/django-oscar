from collections import OrderedDict

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.translation import ugettext_lazy as _

from oscar.apps.search import facets

FACET_COUNTS = {
    u'dates': {},
    u'fields': {
        'category': [('Fiction', 12), ('Horror', 6), ('Comedy', 3)],
        'product_class': [('Book', 18), ('DVD', 3)],
        'rating': [],
    },
    u'queries': {
        u'price_exact:[0 TO 20]': 15,
        u'price_exact:[20 TO 40]': 5,
        u'price_exact:[40 TO 60]': 1,
        u'price_exact:[60 TO *]': 0,
    }
}


FACET_COUNTS_WITH_PRICE_RANGE_SELECTED = {
    u'dates': {},
    u'fields': {
        'category': [('Fiction', 12), ('Horror', 6), ('Comedy', 3)],
        'product_class': [('Book', 18), ('DVD', 3)],
        'rating': [],
    },
    u'queries': {
        u'price_exact:[0 TO 20]': 0,
        u'price_exact:[20 TO 40]': 21,
        u'price_exact:[40 TO 60]': 0,
        u'price_exact:[60 TO *]': 0,
    }
}


SEARCH_FACETS = {
    'fields': OrderedDict([
        ('product_class', {'name': _('Type'), 'field': 'product_class'}),
        ('rating', {'name': _('Rating'), 'field': 'rating'}),
        ('category', {'name': _('Category'), 'field': 'category'}),
    ]),
    'queries': OrderedDict([
        ('price_range',
         {
             'name': _('Price range'),
             'field': 'price',
             'queries': [
                 (_('0 to 20'), u'[0 TO 20]'),
                 (_('20 to 40'), u'[20 TO 40]'),
                 (_('40 to 60'), u'[40 TO 60]'),
                 (_('60+'), u'[60 TO *]'),
             ]
         }),
    ]),
}


@override_settings(OSCAR_SEARCH_FACETS=SEARCH_FACETS)
class TestFacetMunger(TestCase):

    def test_with_no_facets_selected(self):
        munger = facets.FacetMunger(
            path='/search?q=test',
            selected_multi_facets={},
            facet_counts=FACET_COUNTS)
        data = munger.facet_data()
        self.assertTrue('category' in data)
        self.assertEqual(3, len(data['category']['results']))

        # Check a sample facet dict has the right keys
        datum = data['category']['results'][0]
        for key in ('count', 'disabled', 'name', 'select_url',
                    'selected', 'show_count'):
            self.assertTrue(key in datum)

        self.assertEqual(datum['count'], 12)
        self.assertEqual(datum['name'], 'Fiction')
        self.assertFalse(datum['selected'])

    def test_pagination_params_are_reset(self):
        munger = facets.FacetMunger(
            path='/search?q=test&page=2',
            selected_multi_facets={},
            facet_counts=FACET_COUNTS)
        data = munger.facet_data()

        # Check a sample facet dict has the right keys
        for facet_data in data.values():
            for result in facet_data['results']:
                self.assertTrue('page' not in result['select_url'])

    def test_with_price_facets_selected(self):
        munger = facets.FacetMunger(
            path='/search?q=test&selected_facets=price_exact%3A%5B20+TO+40%5D',
            selected_multi_facets={'price_exact': [u'[20 TO 40]']},
            facet_counts=FACET_COUNTS_WITH_PRICE_RANGE_SELECTED)
        data = munger.facet_data()

        self.assertTrue('price_range' in data)
        self.assertEqual(4, len(data['price_range']['results']))

        # Check a sample facet dict has the right keys
        datum = data['price_range']['results'][1]
        for key in ('count', 'disabled', 'name', 'deselect_url',
                    'selected', 'show_count'):
            self.assertTrue(key in datum)

        self.assertEqual(datum['count'], 21)
        self.assertTrue(datum['selected'])
