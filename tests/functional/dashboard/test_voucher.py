from django.urls import reverse

from oscar.test.testcases import WebTestCase


class TestVoucherListSearch(WebTestCase):
    is_staff = True

    TEST_CASES = [
        ({}, ["Not in a set"]),
        ({"name": "Bob Smith"}, ['Name matches "Bob Smith"']),
        ({"code": "abcd1234"}, ['Code is "ABCD1234"']),
        ({"offer_name": "Shipping offer"}, ['Offer name matches "Shipping offer"']),
        ({"is_active": True}, ["Is active"]),
        ({"is_active": False}, ["Is inactive"]),
        ({"in_set": True}, ["In a set"]),
        ({"in_set": False}, ["Not in a set"]),
        ({"has_offers": True}, ["Has offers"]),
        ({"has_offers": False}, ["Has no offers"]),
        (
            {
                "name": "Bob Smith",
                "code": "abcd1234",
                "offer_name": "Shipping offer",
                "is_active": True,
                "in_set": True,
                "has_offers": True,
            },
            [
                'Name matches "Bob Smith"',
                'Code is "ABCD1234"',
                'Offer name matches "Shipping offer"',
                "Is active",
                "In a set",
                "Has offers",
            ],
        ),
    ]

    def test_search_filter_descriptions(self):
        url = reverse("dashboard:voucher-list")
        for params, expected_filters in self.TEST_CASES:
            response = self.get(url, params=params)
            self.assertEqual(response.status_code, 200)
            applied_filters = [
                el.text.strip()
                for el in response.html.select(".search-filter-list .badge")
            ]
            self.assertEqual(applied_filters, expected_filters)
