"""Tests for the dashboard orders search. """

import warnings
from bs4 import BeautifulSoup
from django.core.urlresolvers import reverse
from django.test import TestCase
from oscar.core.compat import get_user_model, get_model


User = get_user_model()
SourceType = get_model('payment', 'SourceType')


class TestOrderSearch(TestCase):
    """Test the order search page. """

    USERNAME = "staff"
    EMAIL = "staff@example.com"
    PASSWORD = "password"

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

    def setUp(self):
        self._create_payment_source()
        self._create_staff_account_and_login()

    def test_search_filter_descriptions(self):
        for params, expected_filters in self.TEST_CASES:
            # Need to provide the order number parameter to avoid
            # being short-circuited to "all results".
            if 'order_number' not in params:
                params['order_number'] = ''

            response = self._search_with_params(**params)
            self.assertEqual(response.status_code, 200)
            self._assert_filters(response, expected_filters)

    def _create_payment_source(self):
        """Ensure that a payment source type exists. """
        SourceType.objects.create(name="Visa", code="visa")

    def _create_staff_account_and_login(self):
        """Create a staff account and log in using the test client. """
        self.user = User.objects.create_user(self.USERNAME, self.EMAIL, self.PASSWORD)
        self.user.is_staff = True
        self.user.save()
        result = self.client.login(email=self.EMAIL, password=self.PASSWORD)
        self.assertTrue(result, msg="Could not log in as a staff user.")

    def _search_with_params(self, **kwargs):
        """Perform the search with the specified parameters.

        Keyword arguments are the GET parameters to
        the order-list view.

        Returns:
            HttpResponse

        """
        url = reverse('dashboard:order-list')

        # Django raises a warning about using a naive datetime
        # when querying the Order model.  This occurs because
        # the form field is a date, but the model field is a
        # datetime, so when we convert from a date to a datetime
        # there isn't any timezone information.
        # To avoid halting the test, we suppress the warning.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            return self.client.get(url, kwargs)

    def _assert_filters(self, response, expected_filters):
        """Check filter descriptions displayed on the search results page.

        Arguments:
            response (HttpResponse)
            expected_filters (list)

        Raises:
            AssertionError

        """
        doc = BeautifulSoup(response.content)
        filters = [el.text.strip() for el in doc.select('#filters li')]
        self.assertEqual(filters, expected_filters)
