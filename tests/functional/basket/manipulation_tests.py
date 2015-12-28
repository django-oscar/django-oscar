# encoding: utf-8
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from oscar.test.contextmanagers import mock_signal_receiver
from oscar.test.factories import create_basket, create_product
from oscar.test.testcases import WebTestCase
from oscar.test import factories
from oscar.apps.basket import models
from oscar.apps.basket.signals import basket_addition, basket_removal


class TestAddingToBasket(WebTestCase):

    def test_works_for_standalone_product(self):
        product = factories.ProductFactory()

        with mock_signal_receiver(basket_addition) as addition_receiver:
            detail_page = self.get(product.get_absolute_url())
            response = detail_page.forms['add_to_basket_form'].submit()

            self.assertIsRedirect(response)
            baskets = models.Basket.objects.all()
            self.assertEqual(1, len(baskets))

            basket = baskets[0]
            self.assertEqual(1, basket.num_items)

            self.assertEqual(addition_receiver.call_count, 1)

    def test_works_for_child_product(self):
        parent = factories.ProductFactory(structure='parent', stockrecords=[])
        for x in range(3):
            factories.ProductFactory(parent=parent, structure='child')

        with mock_signal_receiver(basket_addition) as addition_receiver:
            detail_page = self.get(parent.get_absolute_url())
            form = detail_page.forms['add_to_basket_form']
            response = form.submit()

            self.assertIsRedirect(response)
            baskets = models.Basket.objects.all()
            self.assertEqual(1, len(baskets))

            basket = baskets[0]
            self.assertEqual(1, basket.num_items)

            self.assertEqual(addition_receiver.call_count, 1)


class TestBasketVariations(WebTestCase):
    """
    WebTestCase doesn't test javascript.
    These tests do not notice javascript errors in the basket page.

    Here the reference for ``mock_calls``:
    http://www.voidspace.org.uk/python/mock/helpers.html#calls-as-tuples
    """

    def setUp(self):
        super(TestBasketVariations, self).setUp()
        self.basket = create_basket(empty=True)
        self.product_alpha = create_product(title='Άλφα', num_in_stock=10)
        self.product_beta = create_product(title='Βήτα', num_in_stock=10)
        self.basket.add_product(self.product_alpha, quantity=3)
        self.basket.add_product(self.product_beta, quantity=5)
        self.basket.owner = self.user
        self.basket.save()

    def test_basket_partial_removal(self):

        with mock_signal_receiver(basket_removal) as receiver:
            basket_page = self.app.get(
                reverse('basket:summary'), user=self.user)

            # sanity check
            self.assertEqual(
                    int(basket_page.forms[
                            'basket_formset']['form-0-quantity'].value), 3)

            # remove 2 items from the first line
            basket_page.forms['basket_formset']['form-0-quantity'].value = 1
            updated_basket_page = basket_page.forms[
                'basket_formset'].submit('submit-0-quantity').follow()

            self.assertEqual(receiver.call_count, 1)

            name, args, kwargs = receiver.mock_calls[0]
            self.assertEqual(kwargs['quantity'], 2)
            self.assertEqual(
                int(updated_basket_page.forms[
                    'basket_formset']['form-0-quantity'].value), 1)

    def test_basket_addition(self):

        with mock_signal_receiver(basket_addition) as receiver:
            basket_page = self.app.get(
                reverse('basket:summary'), user=self.user)
            basket_formset = basket_page.forms['basket_formset']
            # add 2 items to the first line
            basket_formset['form-0-quantity'].value = 5
            updated_basket_page = basket_formset.submit(
                    'submit-0-quantity').follow()
            self.assertEqual(receiver.call_count, 1)

            name, args, kwargs = receiver.mock_calls[0]
            self.assertEqual(kwargs['quantity'], 2)
            self.assertEqual(
                int(updated_basket_page.forms[
                        'basket_formset']['form-0-quantity'].value), 5)

    def test_basket_line_removal(self):

        self.assertEqual(self.basket.lines.count(), 2)

        with mock_signal_receiver(basket_removal) as receiver:
            basket_page = self.app.get(
                reverse('basket:summary'), user=self.user)
            basket_page.forms[
                'basket_formset']['form-0-DELETE'].checked__set(True)
            basket_page.forms['basket_formset'].submit().follow()
            self.assertEqual(receiver.call_count, 1)

            name, args, kwargs = receiver.mock_calls[0]
            self.assertEqual(kwargs['quantity'], 3)

        self.assertEqual(self.basket.lines.count(), 1)

    def test_basket_line_removal_saves_line_variations(self):

        self.assertEqual(self.basket.lines.count(), 2)

        with mock_signal_receiver(basket_removal) as receiver:
            basket_page = self.app.get(
                reverse('basket:summary'), user=self.user)

            # delete 1st line
            basket_page.forms[
                'basket_formset']['form-0-DELETE'].checked__set(True)

            # change 2nd line quantity
            basket_page.forms['basket_formset']['form-1-quantity'].value = 2

            basket_page.forms['basket_formset'].submit().follow()

            self.assertEqual(receiver.call_count, 2)

            # we should receive 2 calls with quantity 3
            for mock_call in receiver.mock_calls:
                name, args, kwargs = mock_call
                self.assertEqual(kwargs['quantity'], 3)

        self.assertEqual(self.basket.lines.count(), 1)

    def test_basket_save_for_later(self):
        """
        """
        self.assertEqual(self.basket.lines.count(), 2)

        with mock_signal_receiver(basket_removal) as receiver:
            basket_page = self.app.get(
                reverse('basket:summary'), user=self.user)
            # save for later
            basket_page.forms[
                'basket_formset']['form-0-save_for_later'].checked__set(True)
            updated_basket_page = basket_page.forms[
                'basket_formset'].submit().follow()

            self.assertEqual(receiver.call_count, 1)
            name, args, kwargs = receiver.mock_calls[0]
            self.assertEqual(kwargs['quantity'], 3)

        self.assertEqual(self.basket.lines.count(), 1)

        with mock_signal_receiver(basket_addition) as receiver:
            # move line to basket again
            save_for_later_form = updated_basket_page.forms[
                'saved_basket_formset']
            save_for_later_form['saved-0-move_to_basket'].checked__set(True)
            save_for_later_form.submit().follow()
            self.assertEqual(receiver.call_count, 1)

            name, args, kwargs = receiver.mock_calls[0]
            self.assertEqual(kwargs['quantity'], 3)

        self.assertEqual(self.basket.lines.count(), 2)

    def test_save_for_later_disregards_basket_variations(self):
        """
        """
        self.assertEqual(self.basket.lines.count(), 2)

        with mock_signal_receiver(basket_removal) as receiver:
            basket_page = self.app.get(
                reverse('basket:summary'), user=self.user)
            # save for later
            basket_page.forms[
                'basket_formset']['form-0-save_for_later'].checked__set(True)

            # basket variation
            basket_page.forms['basket_formset']['form-0-quantity'].value = 1

            updated_basket_page = basket_page.forms[
                'basket_formset'].submit().follow()
            self.assertEqual(receiver.call_count, 1)

            # now the beta product is on the first line
            self.assertEqual(
                int(updated_basket_page.forms[
                    'basket_formset']['form-0-quantity'].value), 5)
