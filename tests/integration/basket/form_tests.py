from decimal import Decimal as D

from django.test import TestCase
from django.conf import settings
import mock

from oscar.apps.basket import forms
from oscar.apps.offer.utils import Applicator
from oscar.core.loading import get_model
from oscar.test import factories
from oscar.test.basket import add_product
from oscar.test.factories import (
    BenefitFactory, ConditionalOfferFactory, ConditionFactory, RangeFactory)


Line = get_model('basket', 'Line')


class TestBasketLineForm(TestCase):

    def setUp(self):
        self.applicator = Applicator()
        rng = RangeFactory(includes_all_products=True)
        self.condition = ConditionFactory(
            range=rng, type=ConditionFactory._meta.model.VALUE,
            value=D('100'), proxy_class=None)
        self.benefit = BenefitFactory(
            range=rng, type=BenefitFactory._meta.model.FIXED,
            value=D('10'), max_affected_items=1)
        self.basket = factories.create_basket()
        self.line = self.basket.all_lines()[0]

    def mock_availability_return_value(self, is_available, reason=''):
        policy = self.line.purchase_info.availability
        policy.is_purchase_permitted = mock.MagicMock(
            return_value=(is_available, reason))

    def build_form(self, quantity=None):
        if quantity is None:
            quantity = self.line.quantity
        return forms.BasketLineForm(
            strategy=self.basket.strategy,
            data={'quantity': quantity},
            instance=self.line)

    def test_enforces_availability_policy_for_valid_quantities(self):
        self.mock_availability_return_value(True)
        form = self.build_form()
        self.assertTrue(form.is_valid())

    def test_enforces_availability_policy_for_invalid_quantities(self):
        self.mock_availability_return_value(False, "Some reason")
        form = self.build_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['quantity'], ['Some reason'])

    def test_skips_availability_policy_for_zero_quantities(self):
        self.mock_availability_return_value(True)
        form = self.build_form(quantity=0)
        self.assertTrue(form.is_valid())

    def test_enforces_max_line_quantity_for_new_product(self):
        invalid_qty = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD + 1
        form = self.build_form(quantity=invalid_qty)
        self.assertFalse(form.is_valid())

    def test_enforce_max_line_quantity_for_existing_product(self):
        settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD = 10
        self.basket.flush()
        product = factories.create_product(num_in_stock=20)
        add_product(self.basket, D('100'), 4, product)
        self.line = self.basket.all_lines()[0]
        form = self.build_form(quantity=6)
        self.assertTrue(form.is_valid())
        form.save()
        form = self.build_form(quantity=11)
        self.assertFalse(form.is_valid())

    def test_basketline_formset_ordering(self):
        # when we use a unordered queryset in the Basketlineformset, the
        # discounts will be lost because django will query the database
        # again to enforce ordered results
        add_product(self.basket, D('100'), 5)
        offer = ConditionalOfferFactory(
            pk=1, condition=self.condition, benefit=self.benefit)

        # now we force an unordered queryset so we can see that our discounts
        # will disappear due to a new ordering query (see django/forms/model.py)
        default_line_ordering = Line._meta.ordering
        Line._meta.ordering = []
        self.basket._lines = self.basket.lines.all()

        self.applicator.apply_offers(self.basket, [offer])
        formset = forms.BasketLineFormSet(
            strategy=self.basket.strategy,
            queryset=self.basket.all_lines())

        # the discount is in all_lines():
        self.assertTrue(self.basket.all_lines()[0].has_discount)

        # but not in the formset
        self.assertFalse(formset.forms[0].instance.has_discount)

        # Restore the ordering on the line
        Line._meta.ordering = default_line_ordering

        # clear the cached lines and apply the offer again
        self.basket._lines = None
        self.applicator.apply_offers(self.basket, [offer])

        formset = forms.BasketLineFormSet(
            strategy=self.basket.strategy,
            queryset=self.basket.all_lines())
        self.assertTrue(formset.forms[0].instance.has_discount)


class TestAddToBasketForm(TestCase):

    def test_allows_a_product_quantity_to_be_increased(self):
        basket = factories.create_basket()
        product = basket.all_lines()[0].product

        # Add more of the same product
        data = {'quantity': 1}
        form = forms.AddToBasketForm(
            basket=basket, product=product, data=data)
        self.assertTrue(form.is_valid())

    def test_checks_whether_passed_product_id_matches_a_real_product(self):
        basket = factories.create_basket()
        product = basket.all_lines()[0].product

        # Add more of the same product
        data = {'quantity': -1}
        form = forms.AddToBasketForm(
            basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())

    def test_checks_if_purchase_is_permitted(self):
        basket = factories.BasketFactory()
        product = factories.ProductFactory()

        # Build a 4-level mock monster so we can force the return value of
        # whether the product is available to buy. This is a serious code smell
        # and needs to be remedied.
        info = mock.Mock()
        info.availability = mock.Mock()
        info.availability.is_purchase_permitted = mock.Mock(
            return_value=(False, "Not on your nelly!"))
        basket.strategy.fetch_for_product = mock.Mock(
            return_value=info)

        data = {'quantity': 1}
        form = forms.AddToBasketForm(
            basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual('Not on your nelly!', form.errors['__all__'][0])

    def test_mixed_currency_baskets_are_not_permitted(self):
        # Ensure basket is one currency
        basket = mock.Mock()
        basket.currency = 'GBP'
        basket.num_items = 1

        # Ensure new product has different currency
        info = mock.Mock()
        info.price.currency = 'EUR'
        basket.strategy.fetch_for_product = mock.Mock(
            return_value=info)

        product = factories.ProductFactory()

        data = {'quantity': 1}
        form = forms.AddToBasketForm(
            basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())
