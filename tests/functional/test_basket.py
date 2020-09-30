import datetime
from decimal import Decimal as D
from http import client as http_client
from http.cookies import _unquote

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext

from oscar.apps.basket import reports
from oscar.apps.basket.models import Basket
from oscar.apps.partner import strategy
from oscar.core.compat import get_user_model
from oscar.test import factories
from oscar.test.basket import add_product
from oscar.test.factories import create_product
from oscar.test.testcases import WebTestCase

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
        oscar_open_basket_cookie = _unquote(self.response.test_app.cookies['oscar_open_basket'])
        basket_id = oscar_open_basket_cookie.split(':')[0]
        basket = Basket.objects.get(id=basket_id)
        line = basket.lines.get(product=self.product)
        stockrecord = self.product.stockrecords.all()[0]
        self.assertEqual(stockrecord.price, line.price_excl_tax)


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

    @override_settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=3)
    def test_adding_more_than_threshold_raises(self):
        dummy_product = create_product(price=D('10.00'), num_in_stock=10)
        url = reverse('basket:add', kwargs={'pk': dummy_product.pk})
        post_params = {'product_id': dummy_product.id,
                       'action': 'add',
                       'quantity': 2}
        response = self.app.post(url, params=post_params)
        self.assertIn('oscar_open_basket', response.test_app.cookies)
        post_params = {'product_id': dummy_product.id,
                       'action': 'add',
                       'quantity': 2}
        response = self.app.post(url, params=post_params)

        expected = gettext(
            "Due to technical limitations we are not able to ship more "
            "than %(threshold)d items in one order. Your basket currently "
            "has %(basket)d items."
        ) % ({'threshold': 3, 'basket': 2})
        self.assertIn(expected, response.test_app.cookies['messages'])


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

    def test_moving_to_saved_basket_creates_new(self):
        self.user = factories.UserFactory()
        product = factories.ProductFactory()
        basket = factories.BasketFactory(owner=self.user)
        basket.add_product(product)

        response = self.get(reverse('basket:summary'))
        formset = response.context['formset']
        form = formset.forms[0]

        data = {
            formset.add_prefix('INITIAL_FORMS'): 1,
            formset.add_prefix('TOTAL_FORMS'): 1,
            formset.add_prefix('MIN_FORMS'): 0,
            formset.add_prefix('MAX_NUM_FORMS'): 1,
            form.add_prefix('id'): form.instance.pk,
            form.add_prefix('quantity'): form.initial['quantity'],
            form.add_prefix('save_for_later'): True,
        }
        response = self.post(reverse('basket:summary'), params=data)

        self.assertRedirects(response, reverse('basket:summary'))
        self.assertFalse(Basket.open.get(pk=basket.pk).lines.exists())
        self.assertEqual(Basket.saved.get(owner=self.user).lines.get(
            product=product).quantity, 1)

    def test_moving_to_saved_basket_updates_existing(self):
        self.user = factories.UserFactory()
        product = factories.ProductFactory()

        basket = factories.BasketFactory(owner=self.user)
        basket.add_product(product)

        saved_basket = factories.BasketFactory(owner=self.user,
                                               status=Basket.SAVED)
        saved_basket.add_product(product)

        response = self.get(reverse('basket:summary'))
        formset = response.context['formset']
        form = formset.forms[0]

        data = {
            formset.add_prefix('INITIAL_FORMS'): 1,
            formset.add_prefix('TOTAL_FORMS'): 1,
            formset.add_prefix('MIN_FORMS'): 0,
            formset.add_prefix('MAX_NUM_FORMS'): 1,
            form.add_prefix('id'): form.instance.pk,
            form.add_prefix('quantity'): form.initial['quantity'],
            form.add_prefix('save_for_later'): True,
        }
        response = self.post(reverse('basket:summary'), params=data)

        self.assertRedirects(response, reverse('basket:summary'))
        self.assertFalse(Basket.open.get(pk=basket.pk).lines.exists())
        self.assertEqual(Basket.saved.get(pk=saved_basket.pk).lines.get(
            product=product).quantity, 2)

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


class BasketFormSetTests(WebTestCase):
    csrf_checks = False

    def test_formset_with_removed_line(self):
        products = [create_product() for i in range(3)]
        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()

        add_product(basket, product=products[0])
        add_product(basket, product=products[1])
        add_product(basket, product=products[2])
        response = self.get(reverse('basket:summary'))
        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 3)

        basket.lines.filter(product=products[0]).delete()

        management_form = formset.management_form
        data = {
            formset.add_prefix('INITIAL_FORMS'): management_form.initial['INITIAL_FORMS'],
            formset.add_prefix('MAX_NUM_FORMS'): management_form.initial['MAX_NUM_FORMS'],
            formset.add_prefix('TOTAL_FORMS'): management_form.initial['TOTAL_FORMS'],
            'form-0-quantity': 1,
            'form-0-id': formset.forms[0].instance.id,
            'form-1-quantity': 2,
            'form-1-id': formset.forms[1].instance.id,
            'form-2-quantity': 2,
            'form-2-id': formset.forms[2].instance.id,
        }
        response = self.post(reverse('basket:summary'), params=data)
        self.assertEqual(response.status_code, 302)
        formset = response.follow().context['formset']
        self.assertEqual(len(formset.forms), 2)
        self.assertEqual(len(formset.forms_with_instances), 2)
        self.assertEqual(basket.lines.all()[0].quantity, 2)
        self.assertEqual(basket.lines.all()[1].quantity, 2)

    def test_invalid_formset_with_removed_line(self):
        products = [create_product() for i in range(3)]
        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()

        add_product(basket, product=products[0])
        add_product(basket, product=products[1])
        add_product(basket, product=products[2])
        response = self.get(reverse('basket:summary'))
        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 3)

        basket.lines.filter(product=products[0]).delete()

        stockrecord = products[1].stockrecords.first()
        stockrecord.num_in_stock = 0
        stockrecord.save()

        management_form = formset.management_form
        data = {
            formset.add_prefix('INITIAL_FORMS'): management_form.initial['INITIAL_FORMS'],
            formset.add_prefix('MIN_NUM_FORMS'): management_form.initial['MIN_NUM_FORMS'],
            formset.add_prefix('MAX_NUM_FORMS'): management_form.initial['MAX_NUM_FORMS'],
            formset.add_prefix('TOTAL_FORMS'): management_form.initial['TOTAL_FORMS'],
            'form-0-quantity': 1,
            'form-0-id': formset.forms[0].instance.id,
            'form-1-quantity': 2,
            'form-1-id': formset.forms[1].instance.id,
            'form-2-quantity': 2,
            'form-2-id': formset.forms[2].instance.id,
        }
        response = self.post(reverse('basket:summary'), params=data)
        self.assertEqual(response.status_code, 200)
        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 2)
        self.assertEqual(len(formset.forms_with_instances), 2)
        self.assertEqual(basket.lines.all()[0].quantity, 1)
        self.assertEqual(basket.lines.all()[1].quantity, 1)

    def test_deleting_valid_line_with_other_valid_line(self):
        product_1 = create_product()
        product_2 = create_product()

        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product_1)
        add_product(basket, product=product_2)

        response = self.get(reverse('basket:summary'))
        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 2)

        data = {
            formset.add_prefix('TOTAL_FORMS'): formset.management_form.initial['TOTAL_FORMS'],
            formset.add_prefix('INITIAL_FORMS'): formset.management_form.initial['INITIAL_FORMS'],
            formset.add_prefix('MIN_NUM_FORMS'): formset.management_form.initial['MIN_NUM_FORMS'],
            formset.add_prefix('MAX_NUM_FORMS'): formset.management_form.initial['MAX_NUM_FORMS'],
            formset.forms[0].add_prefix('id'): formset.forms[0].instance.pk,
            formset.forms[0].add_prefix('quantity'): formset.forms[0].instance.quantity,
            formset.forms[0].add_prefix('DELETE'): 'on',
            formset.forms[1].add_prefix('id'): formset.forms[1].instance.pk,
            formset.forms[1].add_prefix('quantity'): formset.forms[1].instance.quantity,
        }
        response = self.post(reverse('basket:summary'), params=data, xhr=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['formset'].forms), 1)
        self.assertFalse(response.context['formset'].is_bound)  # new formset is rendered
        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.lines.all()[0].quantity, 1)

    def test_deleting_valid_line_with_other_invalid_line(self):
        product_1 = create_product()
        product_2 = create_product()

        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product_1)
        add_product(basket, product=product_2)

        response = self.get(reverse('basket:summary'))
        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 2)

        # Render product for other line out of stock
        product_2.stockrecords.update(num_in_stock=0)

        data = {
            formset.add_prefix('TOTAL_FORMS'): formset.management_form.initial['TOTAL_FORMS'],
            formset.add_prefix('INITIAL_FORMS'): formset.management_form.initial['INITIAL_FORMS'],
            formset.add_prefix('MIN_NUM_FORMS'): formset.management_form.initial['MIN_NUM_FORMS'],
            formset.add_prefix('MAX_NUM_FORMS'): formset.management_form.initial['MAX_NUM_FORMS'],
            formset.forms[0].add_prefix('id'): formset.forms[0].instance.pk,
            formset.forms[0].add_prefix('quantity'): formset.forms[0].instance.quantity,
            formset.forms[0].add_prefix('DELETE'): 'on',
            formset.forms[1].add_prefix('id'): formset.forms[1].instance.pk,
            formset.forms[1].add_prefix('quantity'): formset.forms[1].instance.quantity,
        }
        response = self.post(reverse('basket:summary'), params=data, xhr=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['formset'].forms), 1)
        self.assertTrue(response.context['formset'].is_bound)  # formset with errors is rendered
        self.assertFalse(response.context['formset'].forms[0].is_valid())
        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.lines.all()[0].quantity, 1)

    def test_deleting_invalid_line_with_other_valid_line(self):
        product_1 = create_product()
        product_2 = create_product()

        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product_1)
        add_product(basket, product=product_2)

        response = self.get(reverse('basket:summary'))
        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 2)

        # Render product for to-be-deleted line out of stock
        product_1.stockrecords.update(num_in_stock=0)

        data = {
            formset.add_prefix('TOTAL_FORMS'): formset.management_form.initial['TOTAL_FORMS'],
            formset.add_prefix('INITIAL_FORMS'): formset.management_form.initial['INITIAL_FORMS'],
            formset.add_prefix('MIN_NUM_FORMS'): formset.management_form.initial['MIN_NUM_FORMS'],
            formset.add_prefix('MAX_NUM_FORMS'): formset.management_form.initial['MAX_NUM_FORMS'],
            formset.forms[0].add_prefix('id'): formset.forms[0].instance.pk,
            formset.forms[0].add_prefix('quantity'): formset.forms[0].instance.quantity,
            formset.forms[0].add_prefix('DELETE'): 'on',
            formset.forms[1].add_prefix('id'): formset.forms[1].instance.pk,
            formset.forms[1].add_prefix('quantity'): formset.forms[1].instance.quantity,
        }
        response = self.post(reverse('basket:summary'), params=data, xhr=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['formset'].forms), 1)
        self.assertFalse(response.context['formset'].is_bound)  # new formset is rendered
        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.lines.all()[0].quantity, 1)

    def test_deleting_invalid_line_with_other_invalid_line(self):
        product_1 = create_product()
        product_2 = create_product()

        basket = factories.create_basket(empty=True)
        basket.owner = self.user
        basket.save()
        add_product(basket, product=product_1)
        add_product(basket, product=product_2)

        response = self.get(reverse('basket:summary'))
        formset = response.context['formset']
        self.assertEqual(len(formset.forms), 2)

        # Render products for both lines out of stock
        product_1.stockrecords.update(num_in_stock=0)
        product_2.stockrecords.update(num_in_stock=0)

        data = {
            formset.add_prefix('TOTAL_FORMS'): formset.management_form.initial['TOTAL_FORMS'],
            formset.add_prefix('INITIAL_FORMS'): formset.management_form.initial['INITIAL_FORMS'],
            formset.add_prefix('MIN_NUM_FORMS'): formset.management_form.initial['MIN_NUM_FORMS'],
            formset.add_prefix('MAX_NUM_FORMS'): formset.management_form.initial['MAX_NUM_FORMS'],
            formset.forms[0].add_prefix('id'): formset.forms[0].instance.pk,
            formset.forms[0].add_prefix('quantity'): formset.forms[0].instance.quantity,
            formset.forms[0].add_prefix('DELETE'): 'on',
            formset.forms[1].add_prefix('id'): formset.forms[1].instance.pk,
            formset.forms[1].add_prefix('quantity'): formset.forms[1].instance.quantity,
        }
        response = self.post(reverse('basket:summary'), params=data, xhr=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['formset'].forms), 1)
        self.assertTrue(response.context['formset'].is_bound)  # formset with errors is rendered
        self.assertFalse(response.context['formset'].forms[0].is_valid())
        self.assertEqual(basket.lines.count(), 1)
        self.assertEqual(basket.lines.all()[0].quantity, 1)
