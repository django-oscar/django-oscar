import importlib

from dateutil.relativedelta import relativedelta
from mock import patch, call

from django.conf import settings
from django.utils import timezone
from django.test import TestCase, override_settings

from django_elasticsearch_dsl import fields as dsl_fields
from oscar.apps.catalogue.models import Product, ProductAttribute

from oscar.test import factories
from oscar.test.factories import (create_product, create_stockrecord, create_basket,
                                  create_order, ProductFactory)


def ProductDocument(*args, **kwargs):
    documents = importlib.import_module('oscar.apps.catalogue.documents')
    importlib.reload(documents)
    return documents.ProductDocument(*args, **kwargs)


class ProductDocumentTestCase(TestCase):

    def test_get_stockrecord_data(self):
        partner_sku = 'SKU'
        price = 3200
        num_in_stock = 10

        stockrecord = create_stockrecord(partner_sku=partner_sku, price_excl_tax=price,
                                         num_in_stock=num_in_stock)

        expected = {
            'partner': stockrecord.partner.pk,
            'currency': stockrecord.price_currency,
            'price': price,
            'num_in_stock': num_in_stock,
            'sku': partner_sku
        }

        doc = ProductDocument()
        self.assertEqual(doc.get_stockrecord_data(stockrecord), expected)

    def test_only_parent_and_standalone_products_are_indexed(self):
        standalone = create_product(structure=Product.STANDALONE)
        parent = create_product(product_class=ProductFactory(), structure=Product.PARENT)
        child = create_product(parent=parent)

        pd = ProductDocument()
        queryset = pd.get_queryset()

        self.assertIn(standalone, queryset)
        self.assertIn(parent, queryset)
        self.assertNotIn(child, queryset)

    def test_get_stockrecord_data_returns_none_if_stockrecord_has_no_price_excl_tax(self):
        no_price = create_stockrecord()
        no_price.price_excl_tax = None
        no_price.save()

        self.assertIsNone(ProductDocument().get_stockrecord_data(no_price))

    def test_prepare_stock(self):
        product = create_product()

        sr1 = create_stockrecord(product, partner_name="P1", price_excl_tax=1000)
        sr2 = create_stockrecord(product, partner_name="P2", price_excl_tax=2000)

        doc = ProductDocument()
        with patch.object(doc.__class__, 'get_stockrecord_data',
                          return_value='gsd_data') as get_stockrecord_data_mock:
            stock_data = doc.prepare_stock(product)
            get_stockrecord_data_mock.assert_has_calls([call(sr1), call(sr2)], any_order=True)

            self.assertEqual(stock_data, ['gsd_data', 'gsd_data'])

    def test_prepare_stock_skips_parent_products_and_products_without_stockrecords(self):
        doc = ProductDocument()
        self.assertIsNone(doc.prepare_stock(create_product()))

        parent = create_product()
        create_product(parent=parent)

        self.assertIsNone(doc.prepare_stock(parent))

    @override_settings(MONTHS_TO_RUN_ANALYTICS=3)
    def test_get_score_returns_number_of_times_product_has_been_ordered_within_specified_period(self):
        product = create_product(price=1000)

        basket1 = create_basket(empty=True)
        basket1.add_product(product)
        create_order(basket=basket1)

        basket2 = create_basket(empty=True)
        basket2.add_product(product)
        create_order(basket=basket2)

        # this order shouldn't be counted
        basket3 = create_basket(empty=True)
        basket3.add_product(product)
        order3 = create_order(basket=basket3)
        order3.date_placed = timezone.now() - relativedelta(months=4)
        order3.save()

        self.assertEqual(ProductDocument().prepare_score(product), 2)

    def test_get_categories_returns_pks_of_all_categories_product_belongs_to_including_the_category_ancestors(self):
        product = create_product()

        # tree 1
        tr1_root = factories.CategoryFactory()
        tr1_parent = tr1_root.add_child()
        tr1_category = tr1_parent.add_child()
        factories.ProductCategoryFactory(category=tr1_category, product=product)

        # tree 2
        tr2_root = factories.CategoryFactory()
        tr2_parent = tr2_root.add_child()
        tr2_category = tr2_parent.add_child()
        factories.ProductCategoryFactory(category=tr2_category, product=product)

        expected_categories = [
            tr1_root.pk, tr2_root.pk,
            tr1_parent.pk, tr2_parent.pk,
            tr1_category.pk, tr2_category.pk
        ]

        self.assertEqual(
            sorted(ProductDocument().prepare_categories(product)),
            sorted(expected_categories)
        )

    def test_es_dsl_fields_created_for_product_attributes_in_ELASTICSEARCH_FACETS(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()
        OSCAR_SEARCH['FACETS'] = {'included_attribute': {}}

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            ProductAttribute.objects.create(
                name='Test attribute', code='included_attribute',
                type=ProductAttribute.TEXT
            )
            ProductAttribute.objects.create(
                name='Test attribute', code='not_included_attribute',
                type=ProductAttribute.TEXT
            )

            doc = ProductDocument()

            variants = doc._doc_type._fields()['variants']

            self.assertTrue(isinstance(variants.properties['included_attribute'], dsl_fields.KeywordField))

            self.assertFalse(hasattr(variants.properties, 'not_included_attribute'))

    def test_prepared_data_contains_attribute_data(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()
        OSCAR_SEARCH['FACETS'] = {'attribute_one': {}, 'attribute_two': {}}

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):

            product_class = factories.ProductClassFactory()

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Attribute 1', code='attribute_one',
                type=ProductAttribute.TEXT
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Attribute 2', code='attribute_two',
                type=ProductAttribute.FLOAT
            ))

            product = create_product(attributes={
                'attribute_one': 'Hello world',
                'attribute_two': 16.1
            })

            doc = ProductDocument()

            prepared_data = doc.prepare(product)
            self.assertEqual(prepared_data['variants'][0]['attribute_one'], 'Hello world')
            self.assertEqual(prepared_data['variants'][0]['attribute_two'], 16.1)

    def test_proper_fields_used_for_different_attribute_types(self):
        OSCAR_SEARCH = settings.OSCAR_SEARCH.copy()
        OSCAR_SEARCH['FACETS'] = {
            'text': {},
            'integer': {},
            'boolean': {},
            'float': {},
            'richtext': {},
            'date': {},
            'datetime': {},
            'option': {},
            'multi_option': {}
        }

        with override_settings(OSCAR_SEARCH=OSCAR_SEARCH):
            product_class = factories.ProductClassFactory()

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Text', code='text',
                type=ProductAttribute.TEXT
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Integer', code='integer',
                type=ProductAttribute.INTEGER
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Boolean', code='boolean',
                type=ProductAttribute.BOOLEAN
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Float', code='float',
                type=ProductAttribute.FLOAT
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Richtext', code='richtext',
                type=ProductAttribute.RICHTEXT
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Date', code='date',
                type=ProductAttribute.DATE
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Datetime', code='datetime',
                type=ProductAttribute.DATETIME
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Option', code='option',
                type=ProductAttribute.OPTION
            ))

            product_class.attributes.add(ProductAttribute.objects.create(
                name='Multi Option', code='multi_option',
                type=ProductAttribute.MULTI_OPTION
            ))

            doc = ProductDocument()

            def get_variant(field_name):
                return doc.__class__._doc_type._fields()['variants'].properties[field_name]

            self.assertTrue(isinstance(doc.__class__._doc_type._fields()['variants'], dsl_fields.ObjectField))
            self.assertTrue(isinstance(get_variant('text'), dsl_fields.KeywordField))
            self.assertTrue(isinstance(get_variant('integer'), dsl_fields.IntegerField))
            self.assertTrue(isinstance(get_variant('boolean'), dsl_fields.BooleanField))
            self.assertTrue(isinstance(get_variant('float'), dsl_fields.FloatField))
            self.assertTrue(isinstance(get_variant('richtext'), dsl_fields.KeywordField))
            self.assertTrue(isinstance(get_variant('date'), dsl_fields.DateField))
            self.assertTrue(isinstance(get_variant('datetime'), dsl_fields.DateField))
            self.assertTrue(isinstance(get_variant('option'), dsl_fields.KeywordField))
            self.assertTrue(isinstance(get_variant('multi_option'), dsl_fields.KeywordField))

    def test_get_attribute_data_returns_proper_value_for_multi_options(self):
        option_group = factories.AttributeOptionGroupFactory()
        multi_option = factories.ProductAttributeFactory(
            type='multi_option',
            name='Sizes',
            code='sizes',
            option_group=option_group
        )

        options = factories.AttributeOptionFactory.create_batch(
            3, group=option_group)

        product = create_product()
        multi_option.save_value(product, [options[0], options[1]])
        product.refresh_from_db()

        doc = ProductDocument()
        self.assertEqual(
            sorted(doc.get_attribute_data(product, 'sizes')),
            sorted([options[0].option, options[1].option])
        )

    def test_get_attribute_data_returns_proper_value_for_option(self):
        option_group = factories.AttributeOptionGroupFactory()
        option = factories.ProductAttributeFactory(
            type='option',
            name='Option',
            code='option',
            option_group=option_group
        )
        options = factories.AttributeOptionFactory.create_batch(
            3, group=option_group)

        product = create_product()
        option.save_value(product, options[1])

        doc = ProductDocument()
        self.assertEqual(
            doc.get_attribute_data(product, 'option'),
            options[1].option
        )

    def test_sanitize_description_strips_tags_and_turns_white_space_to_single_space(self):
        initial_description = """<some-tag>First text</some-tag>

        Second text"""

        expected_description = "First text Second text"

        doc = ProductDocument()
        self.assertEqual(
            doc.sanitize_description(initial_description),
            expected_description
        )

    def test_descriptions_are_sanitized(self):
        description = "description"

        product = create_product(description=description)

        doc = ProductDocument()
        with patch.object(doc.__class__, 'sanitize_description') as sanitize_mock:
            doc.prepare_description(product)
            sanitize_mock.assert_called_with(description)

    def test_stockrecords_added_from_child_products(self):
        parent = create_product(product_class=ProductFactory(), structure=Product.PARENT)
        child = create_product(parent=parent)

        child_stock = create_stockrecord(child, partner_name="P1", price_excl_tax=1000)

        doc = ProductDocument()

        self.assertEqual(
            doc.prepare_stock(parent),
            [doc.get_stockrecord_data(child_stock)]
        )
