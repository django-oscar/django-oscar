from decimal import Decimal as D
import httplib
import datetime

from django.contrib.auth.models import User
from django.conf import settings
from django.test import TestCase, Client
from django.core.urlresolvers import reverse

from oscar_testsupport.factories import create_product
from oscar.apps.basket.models import Basket
from oscar.apps.basket import reports


class BasketMergingTests(TestCase):

    def setUp(self):
        self.product = create_product()
        self.user_basket = Basket()
        self.user_basket.add_product(self.product)
        self.cookie_basket = Basket()
        self.cookie_basket.add_product(self.product, 2)
        self.user_basket.merge(self.cookie_basket, add_quantities=False)

    def test_cookie_basket_has_status_set(self):
        self.assertEqual('Merged', self.cookie_basket.status)

    def test_lines_are_moved_across(self):
        self.assertEqual(1, self.user_basket.lines.all().count())

    def test_merge_line_takes_max_quantity(self):
        line = self.user_basket.lines.get(product=self.product)
        self.assertEqual(2, line.quantity)


class AnonAddToBasketViewTests(TestCase):

    def setUp(self):
        self.product = create_product(price=D('10.00'))
        url = reverse('basket:add')
        post_params = {'product_id': self.product.id,
                       'action': 'add',
                       'quantity': 1}
        self.client = Client()
        self.response = self.client.post(url, post_params)

    def test_cookie_is_created(self):
        self.assertTrue('oscar_open_basket' in self.response.cookies)

    def test_price_is_recorded(self):
        basket_id = self.response.cookies['oscar_open_basket'].value.split('_')[0]
        basket = Basket.objects.get(id=basket_id)
        line = basket.lines.get(product=self.product)
        self.assertEqual(self.product.stockrecord.price_incl_tax, line.price_incl_tax)


class BasketSummaryViewTests(TestCase):

    def setUp(self):
        url = reverse('basket:summary')
        self.response = self.client.get(url)

    def test_shipping_method_in_context(self):
        self.assertTrue('shipping_method' in self.response.context)

    def test_order_total_in_context(self):
        self.assertTrue('order_total_incl_tax' in self.response.context)

    def test_view_does_not_error(self):
        self.assertEquals(httplib.OK, self.response.status_code)

    def test_basket_in_context(self):
        self.assertTrue('basket' in self.response.context)

    def test_basket_is_empty(self):
        basket = self.response.context['basket']
        self.assertEquals(0, basket.num_lines)


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


class SavedBasketTests(TestCase):

    def test_moving_from_saved_basket(self):
        user = User.objects.create_user(username='test', password='pass',
                                        email='test@example.com')
        client = Client()
        client.login(username=user.username, password='pass')

        product = create_product(price=D('10.00'), num_in_stock=2)
        basket, created = Basket.open.get_or_create(owner=user)
        basket.add_product(product=product, quantity=1)

        saved_basket, created = Basket.saved.get_or_create(owner=user)
        saved_basket.add_product(product=product, quantity=1)

        response = client.get(reverse('basket:summary'))
        saved_formset = response.context['saved_formset']
        saved_form = saved_formset.forms[0]

        data = {
            saved_formset.add_prefix('INITIAL_FORMS'): 1,
            saved_formset.add_prefix('MAX_NUM_FORMS'): 1,
            saved_formset.add_prefix('TOTAL_FORMS'): 1,
            saved_form.add_prefix('id'): saved_form.initial['id'],
            saved_form.add_prefix('move_to_basket'): True,
        }
        response = client.post(reverse('basket:saved'), data=data)
        self.assertEqual(Basket.open.get(id=basket.id).lines.get(product=product).quantity, 2)
        self.assertRedirects(response, reverse('basket:summary'))

    def test_moving_from_saved_basket_more_than_stocklevel_raises(self):
        user = User.objects.create_user(username='test', password='pass',
                                        email='test@example.com')
        client = Client()
        client.login(username=user.username, password='pass')

        product = create_product(price=D('10.00'), num_in_stock=1)
        basket, created = Basket.open.get_or_create(owner=user)
        basket.add_product(product=product, quantity=1)

        saved_basket, created = Basket.saved.get_or_create(owner=user)
        saved_basket.add_product(product=product, quantity=1)

        response = client.get(reverse('basket:summary'))
        saved_formset = response.context['saved_formset']
        saved_form = saved_formset.forms[0]

        data = {
            saved_formset.add_prefix('INITIAL_FORMS'): 1,
            saved_formset.add_prefix('MAX_NUM_FORMS'): 1,
            saved_formset.add_prefix('TOTAL_FORMS'): 1,
            saved_form.add_prefix('id'): saved_form.initial['id'],
            saved_form.add_prefix('move_to_basket'): True,
        }
        response = client.post(reverse('basket:saved'), data=data)
        # we can't add more than stock level into basket
        self.assertEqual(Basket.open.get(id=basket.id).lines.get(product=product).quantity, 1)
        self.assertRedirects(response, reverse('basket:summary'))
