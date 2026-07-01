from decimal import Decimal as D
from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings

from oscar.apps.basket import forms, formsets
from oscar.apps.offer.utils import Applicator
from oscar.core.loading import get_model
from oscar.test import factories
from oscar.test.basket import add_product
from oscar.test.factories import (
    AttributeOptionFactory,
    AttributeOptionGroupFactory,
    BenefitFactory,
    ConditionalOfferFactory,
    ConditionFactory,
    OptionFactory,
    RangeFactory,
)
from oscar.test.factories.catalogue import ProductFactory

Line = get_model("basket", "Line")
Option = get_model("catalogue", "Option")
Product = get_model("catalogue", "Product")


class TestBasketLineForm(TestCase):
    def setUp(self):
        self.applicator = Applicator()
        rng = RangeFactory(includes_all_products=True)
        self.condition = ConditionFactory(
            range=rng,
            type=ConditionFactory._meta.model.VALUE,
            value=D("100"),
            proxy_class=None,
        )
        self.benefit = BenefitFactory(
            range=rng,
            type=BenefitFactory._meta.model.FIXED,
            value=D("10"),
            max_affected_items=1,
        )
        self.basket = factories.create_basket()
        self.line = self.basket.all_lines()[0]

    def mock_availability_return_value(self, is_available, reason=""):
        policy = self.line.purchase_info.availability
        policy.is_purchase_permitted = mock.MagicMock(
            return_value=(is_available, reason)
        )

    def build_form(self, quantity=None):
        if quantity is None:
            quantity = self.line.quantity
        return forms.BasketLineForm(
            strategy=self.basket.strategy,
            data={"quantity": quantity},
            instance=self.line,
        )

    def test_interpret_empty_quantity_field_as_zero(self):
        form = self.build_form(quantity="")

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["quantity"], 0)

    def test_enforces_availability_policy_for_valid_quantities(self):
        self.mock_availability_return_value(True)
        form = self.build_form()
        self.assertTrue(form.is_valid())

    def test_enforces_availability_policy_for_invalid_quantities(self):
        self.mock_availability_return_value(False, "Some reason")
        form = self.build_form()
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["quantity"], ["Some reason"])

    def test_skips_availability_policy_for_zero_quantities(self):
        self.mock_availability_return_value(True)
        form = self.build_form(quantity=0)
        self.assertTrue(form.is_valid())

    def test_enforces_max_line_quantity_for_new_product(self):
        invalid_qty = settings.OSCAR_MAX_BASKET_QUANTITY_THRESHOLD + 1
        form = self.build_form(quantity=invalid_qty)
        self.assertFalse(form.is_valid())

    @override_settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=10)
    def test_enforce_max_line_quantity_for_existing_product(self):
        self.basket.flush()
        product = factories.create_product(num_in_stock=20)
        add_product(self.basket, D("100"), 4, product)
        self.line = self.basket.all_lines()[0]
        form = self.build_form(quantity=6)
        self.assertTrue(form.is_valid())
        form.save()
        # We set the _lines to None because the basket caches the lines here.
        # We want the basket to do the query again.
        # basket.num_items() will otherwise not return the correct values
        self.basket._lines = None
        form = self.build_form(quantity=11)
        self.assertFalse(form.is_valid())

    def test_line_quantity_max_attribute_per_num_available(self):
        self.basket.flush()
        product = factories.create_product(num_in_stock=20)
        add_product(self.basket, D("100"), 4, product)
        self.line = self.basket.all_lines()[0]
        form = self.build_form()
        self.assertIn('max="20"', str(form["quantity"]))

    @override_settings(OSCAR_MAX_BASKET_QUANTITY_THRESHOLD=10)
    def test_line_quantity_max_attribute_per_basket_threshold(self):
        self.basket.flush()
        product = factories.create_product(num_in_stock=20)
        add_product(self.basket, D("100"), 4, product)
        self.line = self.basket.all_lines()[0]
        form = self.build_form()
        self.assertIn('max="6"', str(form["quantity"]))

    def test_basketline_formset_ordering(self):
        # when we use a unordered queryset in the Basketlineformset, the
        # discounts will be lost because django will query the database
        # again to enforce ordered results
        add_product(self.basket, D("100"), 5)
        offer = ConditionalOfferFactory(
            pk=1, condition=self.condition, benefit=self.benefit
        )

        # now we force an unordered queryset so we can see that our discounts
        # will disappear due to a new ordering query (see django/forms/model.py)
        default_line_ordering = Line._meta.ordering
        Line._meta.ordering = []
        self.basket._lines = self.basket.lines.all()

        self.applicator.apply_offers(self.basket, [offer])
        formset = formsets.BasketLineFormSet(
            strategy=self.basket.strategy, queryset=self.basket.all_lines()
        )

        # the discount is in all_lines():
        self.assertTrue(self.basket.all_lines()[0].has_discount)

        # but not in the formset
        self.assertFalse(formset.forms[0].instance.has_discount)

        # Restore the ordering on the line
        Line._meta.ordering = default_line_ordering

        # clear the cached lines and apply the offer again
        self.basket._lines = None
        self.applicator.apply_offers(self.basket, [offer])

        formset = formsets.BasketLineFormSet(
            strategy=self.basket.strategy, queryset=self.basket.all_lines()
        )
        self.assertTrue(formset.forms[0].instance.has_discount)

    def test_max_allowed_quantity_with_options(self):
        self.basket.flush()

        option = OptionFactory(required=False)
        product = factories.create_product(num_in_stock=2)
        product.get_product_class().options.add(option)
        self.basket.add_product(
            product, options=[{"option": option, "value": "Test 1"}]
        )
        self.basket.add_product(
            product, options=[{"option": option, "value": "Test 2"}]
        )

        form = forms.BasketLineForm(
            strategy=self.basket.strategy,
            data={"quantity": 2},
            instance=self.basket.all_lines()[0],
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Available stock is only %s, which has been exceeded because multiple lines contain the same product."
            % 2,
            str(form.errors),
        )


class TestAddToBasketForm(TestCase):
    def test_allows_a_product_quantity_to_be_increased(self):
        basket = factories.create_basket()
        product = basket.all_lines()[0].product

        # Add more of the same product
        data = {"quantity": 1}
        form = forms.AddToBasketForm(basket=basket, product=product, data=data)
        self.assertTrue(form.is_valid())

    def test_checks_whether_passed_product_id_matches_a_real_product(self):
        basket = factories.create_basket()
        product = basket.all_lines()[0].product

        # Add more of the same product
        data = {"quantity": -1}
        form = forms.AddToBasketForm(basket=basket, product=product, data=data)
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
            return_value=(False, "Not on your nelly!")
        )
        basket.strategy.fetch_for_product = mock.Mock(return_value=info)

        data = {"quantity": 1}
        form = forms.AddToBasketForm(basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual("Not on your nelly!", form.errors["__all__"][0])

    def test_mixed_currency_baskets_are_not_permitted(self):
        # Ensure basket is one currency
        basket = mock.Mock()
        basket.currency = "GBP"
        basket.num_items = 1

        # Ensure new product has different currency
        info = mock.Mock()
        info.price.currency = "EUR"
        basket.strategy.fetch_for_product = mock.Mock(return_value=info)

        product = factories.ProductFactory()

        data = {"quantity": 1}
        form = forms.AddToBasketForm(basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())

    def test_cannot_add_a_product_without_price(self):
        basket = factories.BasketFactory()
        product = factories.create_product(price=None)

        data = {"quantity": 1}
        form = forms.AddToBasketForm(basket=basket, product=product, data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["__all__"][0],
            "This product cannot be added to the basket because a price "
            "could not be determined for it.",
        )

    def test_add_to_basket_with_children(self):
        parent = ProductFactory(structure=Product.PARENT)
        for i in range(5):
            if i == 0:
                ProductFactory(structure=Product.CHILD, parent=parent, is_public=False)
                continue
            ProductFactory(structure=Product.CHILD, parent=parent)

        random_child = ProductFactory(
            structure=Product.CHILD, parent=ProductFactory(structure=Product.PARENT)
        )

        basket = factories.BasketFactory()

        form = forms.AddToBasketForm(basket=basket, product=parent)
        self.assertEqual(len(form.fields["child_id"].choices), 4)
        choices_child_ids = [choice[0] for choice in form.fields["child_id"].choices]
        self.assertEqual(
            choices_child_ids, [child.id for child in parent.get_public_children()]
        )

        # Without child id, it should not be valid
        data = {"quantity": 1}
        form = forms.AddToBasketForm(basket=basket, product=parent, data=data)
        self.assertFalse(form.is_valid())

        data = {"quantity": 1, "child_id": parent.children.first().id}
        form = forms.AddToBasketForm(basket=basket, product=parent, data=data)
        self.assertTrue(form.is_valid())

        # With random child id, it should not be valid
        data = {"quantity": 1, "child_id": random_child.id}
        form = forms.AddToBasketForm(basket=basket, product=parent, data=data)
        self.assertFalse(form.is_valid())


class TestAddToBasketWithOptionForm(TestCase):
    def setUp(self):
        self.basket = factories.create_basket(empty=True)
        self.product = factories.create_product(num_in_stock=1)

    def _get_basket_form(self, basket, product, data=None):
        return forms.AddToBasketForm(basket=basket, product=product, data=data)

    def test_basket_option_field_exists(self):
        option = OptionFactory()
        self.product.product_class.options.add(option)
        form = self._get_basket_form(basket=self.basket, product=self.product)
        self.assertIn(option.code, form.fields)

    def test_add_to_basket_with_not_required_option(self):
        option = OptionFactory(required=False)
        self.product.product_class.options.add(option)
        data = {"quantity": 1}
        form = self._get_basket_form(
            basket=self.basket,
            product=self.product,
            data=data,
        )
        self.assertTrue(form.is_valid())
        self.assertFalse(form.fields[option.code].required)

    def test_add_to_basket_with_required_option(self):
        option = OptionFactory(required=True)
        self.product.product_class.options.add(option)
        data = {"quantity": 1}
        invalid_form = self._get_basket_form(
            basket=self.basket,
            product=self.product,
            data=data,
        )
        self.assertFalse(invalid_form.is_valid())
        self.assertTrue(invalid_form.fields[option.code].required)
        data[option.code] = "Test value"
        valid_form = self._get_basket_form(
            basket=self.basket,
            product=self.product,
            data=data,
        )
        self.assertTrue(valid_form.is_valid())

    def _test_add_to_basket_with_specific_option_type(
        self, option_type, invalid_value, valid_value
    ):
        if option_type in [
            Option.SELECT,
            Option.RADIO,
            Option.MULTI_SELECT,
            Option.CHECKBOX,
        ]:
            group = AttributeOptionGroupFactory(name="minte")
            AttributeOptionFactory(option="henk", group=group)
            AttributeOptionFactory(option="klaas", group=group)
            option = OptionFactory(required=True, type=option_type, option_group=group)
        else:
            option = OptionFactory(required=True, type=option_type)

        self.product.product_class.options.add(option)
        data = {"quantity": 1, option.code: invalid_value}
        invalid_form = self._get_basket_form(
            basket=self.basket,
            product=self.product,
            data=data,
        )
        self.assertFalse(invalid_form.is_valid())
        data[option.code] = valid_value
        valid_form = self._get_basket_form(
            basket=self.basket,
            product=self.product,
            data=data,
        )
        self.assertTrue(valid_form.is_valid())

    def test_add_to_basket_with_integer_option(self):
        self._test_add_to_basket_with_specific_option_type(
            Option.INTEGER,
            1.55,
            1,
        )

    def test_add_to_basket_with_float_option(self):
        self._test_add_to_basket_with_specific_option_type(
            Option.FLOAT,
            "invalid_float",
            1,
        )

    def test_add_to_basket_with_bool_option(self):
        self._test_add_to_basket_with_specific_option_type(
            Option.BOOLEAN,
            None,
            True,
        )

    def test_add_to_basket_with_date_option(self):
        self._test_add_to_basket_with_specific_option_type(
            Option.DATE,
            "invalid_date",
            "2019-03-03",
        )

    def test_add_to_basket_with_select_option(self):
        self._test_add_to_basket_with_specific_option_type(
            Option.SELECT,
            "invalid_select",
            "henk",
        )

    def test_add_to_basket_with_radio_option(self):
        self._test_add_to_basket_with_specific_option_type(
            Option.RADIO,
            "invalid_radio",
            "henk",
        )

    def test_add_to_basket_with_multi_select_option(self):
        self._test_add_to_basket_with_specific_option_type(
            Option.MULTI_SELECT,
            ["invalid_multi_select"],
            ["henk", "klaas"],
        )

    def test_add_to_basket_with_checkbox_option(self):
        self._test_add_to_basket_with_specific_option_type(
            Option.CHECKBOX,
            ["invalid_checkbox"],
            ["henk", "klaas"],
        )
