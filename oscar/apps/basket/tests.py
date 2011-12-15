from decimal import Decimal as D

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase

from oscar.apps.basket.models import Basket, Line
from oscar.test.helpers import create_product, TwillTestCase


class ViewTest(TwillTestCase):

    def test_for_smoke(self):
        self.visit('basket:summary')
        self.assertResponseCodeIs(200)
        self.assertPageContains('Basket')
        self.assertPageTitleMatches('Oscar')


class BasketModelTest(TestCase):

    def setUp(self):
        self.basket = Basket.objects.create()
        self.dummy_product = create_product()

    def test_empty_baskets_have_zero_lines(self):
        self.assertTrue(Basket().num_lines == 0)

    def test_new_baskets_are_empty(self):
        self.assertTrue(Basket().is_empty)

    def test_basket_have_with_one_line(self):
        Line.objects.create(basket=self.basket, product=self.dummy_product)
        self.assertTrue(self.basket.num_lines == 1)

    def test_add_product_creates_line(self):
        self.basket.add_product(self.dummy_product)
        self.assertTrue(self.basket.num_lines == 1)

    def test_adding_multiproduct_line_returns_correct_number_of_items(self):
        self.basket.add_product(self.dummy_product, 10)
        self.assertEqual(self.basket.num_items, 10)


class BasketViewsTest(TestCase):

    def test_empty_basket_view(self):
        url = reverse('basket:summary')
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
        self.assertEquals(0, response.context['basket'].num_lines)

    def test_anonymous_add_to_basket_creates_cookie(self):
        dummy_product = create_product(price=D('10.00'))
        url = reverse('basket:add')
        post_params = {'product_id': dummy_product.id,
                       'action': 'add',
                       'quantity': 1}
        response = self.client.post(url, post_params)
        self.assertTrue('oscar_open_basket' in response.cookies)


class BasketThresholdTest(TestCase):

    def setUp(self):
        self._old_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = 3

    def tearDown(self):
        settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = self._old_threshold

    def test_adding_more_than_threshold_raises(self):
        dummy_product = create_product(price=D('10.00'))
        url = reverse('basket:add')
        post_params = {'product_id': dummy_product.id,
                       'action': 'add',
                       'quantity': 2}
        response = self.client.post(url, post_params)
        self.assertTrue('oscar_open_basket' in response.cookies)
        post_params = {'product_id': dummy_product.id,
                       'action': 'add',
                       'quantity': 2}
        response = self.client.post(url, post_params)
        self.assertTrue('Your basket currently has 2 items.' in
                        response.cookies['messages'].value)
