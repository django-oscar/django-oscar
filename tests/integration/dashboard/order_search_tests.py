"""Tests for the dashboard orders search. """
from django.core.urlresolvers import reverse

from oscar.test.factories import SourceTypeFactory
from oscar.test.testcases import WebTestCase


class TestOrderSearch(WebTestCase):
    """Test the order search page. """
    is_staff = True

    TEST_CASES = [
        ({}, []),
        (
            {'order_number': 'abcd1234'},
            ['Order number starts with "abcd1234"']
        ),
        (
            {'name': 'Bob Smith'},
            ['Customer name matches "Bob Smith"']
        ),
        (
            {'product_title': 'The Art of War'},
            ['Product name matches "The Art of War"']
        ),
        (
            {'upc': 'abcd1234'},
            ['Includes an item with UPC "abcd1234"']
        ),
        (
            {'partner_sku': 'abcd1234'},
            ['Includes an item with partner SKU "abcd1234"']
        ),
        (
            {'date_from': '2015-01-01'},
            ['Placed after 2015-01-01']
        ),
        (
            {'date_to': '2015-01-01'},
            ['Placed before 2015-01-02']
        ),
        (
            {'date_from': '2014-01-02', 'date_to': '2015-03-04'},
            ['Placed between 2014-01-02 and 2015-03-04']
        ),
        (
            {'voucher': 'abcd1234'},
            ['Used voucher code "abcd1234"']
        ),
        (
            {'payment_method': 'visa'},
            ['Paid using Visa']
        ),
        (
            # Assumes that the test settings (OSCAR_ORDER_STATUS_PIPELINE)
            # include a state called 'A'
            {'status': 'A'},
            ['Order status is A']
        ),
        (
            {
                'name': 'Bob Smith',
                'product_title': 'The Art of War',
                'upc': 'upc_abcd1234',
                'partner_sku': 'partner_avcd1234',
                'date_from': '2014-01-02',
                'date_to': '2015-03-04',
                'voucher': 'voucher_abcd1234',
                'payment_method': 'visa',
                'status': 'A'
            },
            [
                'Customer name matches "Bob Smith"',
                'Product name matches "The Art of War"',
                'Includes an item with UPC "upc_abcd1234"',
                'Includes an item with partner SKU "partner_avcd1234"',
                'Placed between 2014-01-02 and 2015-03-04',
                'Used voucher code "voucher_abcd1234"',
                'Paid using Visa',
                'Order status is A',
            ]
        ),
    ]


    def test_search_filter_descriptions(self):
        SourceTypeFactory(name='Visa', code='visa')
        url = reverse('dashboard:order-list')
        for params, expected_filters in self.TEST_CASES:

            # Need to provide the order number parameter to avoid
            # being short-circuited to "all results".
            params.setdefault('order_number', '')

            response = self.get(url, params=params)
            self.assertEqual(response.status_code, 200)
            applied_filters = [
                el.text.strip() for el in
                response.html.select('.search-filter-list .label')
            ]
            assert applied_filters == expected_filters
