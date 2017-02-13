from decimal import Decimal as D
from django.utils.six.moves import http_client
import datetime

from django.conf import settings
from django.test import TestCase
from django.utils.translation import ugettext
from django.core.urlresolvers import reverse

from oscar.test.factories import create_product
from oscar.core.compat import get_user_model
from oscar.test import factories
from oscar.test.basket import add_product
from oscar.test.utils import extract_cookie_value
from oscar.apps.basket import reports
from oscar.apps.basket.models import Basket
from oscar.test.testcases import WebTestCase
from oscar.apps.partner import strategy


User = get_user_model()


class TestBasketMerging(TestCase):

    def setUp(self):
        self.product = create_product(num_in_stock=10)
        self.user_basket = Basket()
        self.user_basket.strategy = strategy.Default()
        add_product(self.user_basket, product=self.product)
        self.cookie_basket = Basket()
        self.cookie_basket.strategy = strategy.Default()
        add_product(self.cookie_basket, quantity=2, product=self.product)
        self.user_basket.merge(self.cookie_basket, add_quantities=False)

    def test_cookie_basket_has_status_set(self):
        self.assertEqual(Basket.MERGED, self.cookie_basket.status)

    def test_lines_are_moved_across(self):
        self.assertEqual(1, self.user_basket.lines.all().count())

    def test_merge_line_takes_max_quantity(self):
        line = self.user_basket.lines.get(product=self.product)
        self.assertEqual(2, line.quantity)


class AnonAddToBasketViewTests(WebTestCase):
    csrf_checks = False

    def setUp(self):
        self.product = create_product(
            price=D('10.00'), num_in_stock=10)
        url = reverse('basket:add', kwargs={'pk': self.product.pk})
        post_params = {'product_id': self.product.id,
                       'action': 'add',
                       'quantity': 1}
        self.response = self.app.post(url, params=post_params)

    def test_cookie_is_created(self):
        self.assertTrue('oscar_open_basket' in self.response.test_app.cookies)

    def test_price_is_recorded(self):
        oscar_open_basket_cookie = extract_cookie_value(
            self.response.test_app.cookies, 'oscar_open_basket'
        )
        basket_id = oscar_open_basket_cookie.split(':')[0]
        basket = Basket.objects.get(id=basket_id)
        line = basket.lines.get(product=self.product)
        stockrecord = self.product.stockrecords.all()[0]
        self.assertEqual(stockrecord.price_excl_tax, line.price_excl_tax)


class BasketSummaryViewTests(WebTestCase):

    def setUp(self):
        url = reverse('basket:summary')
        self.response = self.app.get(url)

    def test_shipping_method_in_context(self):
        self.assertTrue('shipping_method' in self.response.context)

    def test_order_total_in_context(self):
        self.assertTrue('order_total' in self.response.context)

    def test_view_does_not_error(self):
        self.assertEqual(http_client.OK, self.response.status_code)

    def test_basket_in_context(self):
        self.assertTrue('basket' in self.response.context)

    def test_basket_is_empty(self):
        basket = self.response.context['basket']
        self.assertEqual(0, basket.num_lines)


class BasketThresholdTest(WebTestCase):
    csrf_checks = False

    def setUp(self):
        self._old_threshold = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD
        settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = 3

    def tearDown(self):
        settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = self._old_threshold

    def test_adding_more_than_threshold_raises(self):
        dummy_product = create_product(price=D('10.00'), num_in_stock=10)
        url = reverse('basket:add', kwargs={'pk': dummy_product.pk})
        post_params = {'product_id': dummy_product.id,
                       'action': 'add',
                       'quantity': 2}
        response = self.app.post(url, params=post_params)
        self.assertTrue('oscar_open_basket' in response.test_app.cookies)
        post_params = {'product_id': dummy_product.id,
                       'action': 'add',
                       'quantity': 2}
        response = self.app.post(url, params=post_params)

        expected = ugettext(
            "Due to technical limitations we are not able to ship more "
            "than %(threshold)d items in one order. Your basket currently "
            "has %(basket)d items."
        ) % ({'threshold': 3, 'basket': 2})
        self.assertTrue(expected in response.test_app.cookies['messages'])


class BasketReportTests(TestCase):

    def test_open_report_doesnt_error(self):
        data = {
            'start_date': datetime.date(2012, 5, 1),
            'end_date': datetime.date(2012, 5, 17),
            'formatter': 'CSV'
        }
        generator = reports.OpenBasketReportGenerator(**data)
        generator.generate()

    def test_submitted_report_doesnt_error(self):
        data = {
            'start_date': datetime.date(2012, 5, 1),
            'end_date': datetime.date(2012, 5, 17),
            'formatter': 'CSV'
        }
        generator = reports.SubmittedBasketReportGenerator(**data)
        generator.generate()


class SavedBasketTests(WebTestCase):
    csrf_checks = False

    def test_moving_from_saved_basket(self):
        self.user = User.objects.create_user(username='test', password='pass',
                                             email='test@example.com')
        product = create_product(price=D('10.00'), num_in_stock=2)
        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product)

        saved_basket, created = Basket.saved.get_or_create(owner=self.user)
        saved_basket.strategy = basket.strategy
        add_product(saved_basket, product=product)

        response = self.get(reverse('basket:summary'))
        saved_formset = response.context['saved_formset']
        saved_form = saved_formset.forms[0]

        data = {
            saved_formset.add_prefix('INITIAL_FORMS'): 1,
            saved_formset.add_prefix('MAX_NUM_FORMS'): 1,
            saved_formset.add_prefix('TOTAL_FORMS'): 1,
            saved_form.add_prefix('id'): saved_form.initial['id'],
            saved_form.add_prefix('move_to_basket'): True,
        }
        response = self.post(reverse('basket:saved'), params=data)
        self.assertEqual(Basket.open.get(id=basket.id).lines.get(
            product=product).quantity, 2)
        self.assertRedirects(response, reverse('basket:summary'))

    def test_moving_from_saved_basket_more_than_stocklevel_raises(self):
        self.user = User.objects.create_user(username='test', password='pass',
                                             email='test@example.com')
        product = create_product(price=D('10.00'), num_in_stock=1)
        basket, created = Basket.open.get_or_create(owner=self.user)
        add_product(basket, product=product)

        saved_basket, created = Basket.saved.get_or_create(owner=self.user)
        add_product(saved_basket, product=product)

        response = self.get(reverse('basket:summary'))
        saved_formset = response.context['saved_formset']
        saved_form = saved_formset.forms[0]

        data = {
            saved_formset.add_prefix('INITIAL_FORMS'): 1,
            saved_formset.add_prefix('MAX_NUM_FORMS'): 1,
            saved_formset.add_prefix('TOTAL_FORMS'): 1,
            saved_form.add_prefix('id'): saved_form.initial['id'],
            saved_form.add_prefix('move_to_basket'): True,
        }
        response = self.post(reverse('basket:saved'), params=data)
        # we can't add more than stock level into basket
        self.assertEqual(Basket.open.get(id=basket.id).lines.get(product=product).quantity, 1)
        self.assertRedirects(response, reverse('basket:summary'))
