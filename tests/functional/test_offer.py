from django.test import TestCase

from oscar.test.factories.offer import (
    BenefitFactory,
    ConditionalOfferFactory,
    ConditionFactory,
    RangeFactory,
)
from oscar.test.testcases import WebTestCase


class TestTheOfferListPage(WebTestCase):
    def test_exists(self):
        response = self.app.get("/offers/")
        self.assertEqual(200, response.status_code)


class TestOfferDetailsPageWithUnicodeSlug(TestCase):
    def setUp(self):
        self.slug = "Ûul-wįth-weird-chars"
        self.offer = ConditionalOfferFactory(
            condition=ConditionFactory(), benefit=BenefitFactory(), slug=self.slug
        )

    def test_url_with_unicode_characters(self):
        response = self.client.get(f"/offers/{self.slug}/")
        self.assertEqual(200, response.status_code)


class TestRangeDetailsPageWithUnicodeSlug(TestCase):
    def setUp(self):
        self.slug = "Ûul-wįth-weird-chars"
        self.range = RangeFactory(slug=self.slug, is_public=True)

    def test_url_with_unicode_characters(self):
        response = self.client.get(f"/catalogue/ranges/{self.slug}/")
        self.assertEqual(200, response.status_code)
