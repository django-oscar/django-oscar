from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import ProgrammingError, OperationalError
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.six import with_metaclass

from oscar.apps.catalogue.models import AttributeOption
from oscar.core.loading import get_model

from django_elasticsearch_dsl.documents import DocTypeMeta
from django_elasticsearch_dsl import DocType, fields
from elasticsearch_dsl import Mapping, MetaField


Line = get_model('order', 'Line')
Product = get_model('catalogue', 'Product')
ProductAttribute = get_model('catalogue', 'ProductAttribute')
StockRecord = get_model('partner', 'StockRecord')

product_mapping = Mapping('product')
product_mapping.field('raw_title', 'text', boost=1.25)
product_mapping.field('all_skus', 'text', analyzer='standard')


ATTRIBUTE_TYPE_ES_FIELDS = {
    ProductAttribute.TEXT: fields.KeywordField,
    ProductAttribute.INTEGER: fields.IntegerField,
    ProductAttribute.BOOLEAN: fields.BooleanField,
    ProductAttribute.FLOAT: fields.FloatField,
    ProductAttribute.RICHTEXT: fields.KeywordField,
    ProductAttribute.DATE: fields.DateField,
    ProductAttribute.DATETIME: fields.DateField,
    ProductAttribute.OPTION: fields.KeywordField,
    ProductAttribute.MULTI_OPTION: fields.KeywordField
}


class ProductDocumentMeta(DocTypeMeta):

    def __new__(cls, name, bases, attrs):
        attrs['product_attributes'] = []

        try:
            indexed_attributes = ProductAttribute.objects.filter(code__in=settings.OSCAR_SEARCH.get('FACETS', {}).keys())

            attribute_fields = {}
            for attr in indexed_attributes:
                # don't add it if a custom field is already defined
                if attr.code not in attrs:
                    attribute_fields[attr.code] = ATTRIBUTE_TYPE_ES_FIELDS[attr.type](index='not_analyzed', include_in_all=False)

                attrs['product_attributes'].append(attr.code)

            attrs['variants'] = fields.ListField(field=fields.ObjectField(properties=attribute_fields))

        # without this we can't run migrations on a new database
        except (ProgrammingError, OperationalError):
            pass

        return super(ProductDocumentMeta, cls).__new__(cls, name, bases, attrs)


class ProductDocument(with_metaclass(ProductDocumentMeta, DocType)):

    upc = fields.TextField(
        analyzer="edgengram_analyzer",
        search_analyzer="standard"
    )
    title = fields.TextField(
        analyzer="ngram_analyzer",
        search_analyzer="standard",
        copy_to="raw_title"
    )
    description = fields.TextField(
        analyzer="english"
    )
    stock = fields.ListField(field=fields.NestedField(properties={
        'currency': fields.KeywordField(index='not_analyzed'),
        'sku': fields.KeywordField(copy_to='all_skus'),
        'price': fields.FloatField(),
        'partner': fields.IntegerField(index='not_analyzed'),
        'num_in_stock': fields.IntegerField(index='not_analyzed')
    }, include_in_all=False))
    categories = fields.ListField(field=fields.IntegerField(
        include_in_all=False
    ))
    score = fields.FloatField(include_in_all=False)
    url = fields.TextField(
        index=False,
        attr="get_absolute_url"
    )

    def get_queryset(self):
        qs = super(ProductDocument, self).get_queryset()
        return qs.exclude(structure=Product.CHILD)

    def get_attribute_data(self, product, attribute_name):
        attr = getattr(product.attr, attribute_name, None)
        if isinstance(attr, QuerySet):
            # Multi option, get the list of values directly from database.
            return list(attr.values_list('multi_valued_attribute_values__value_multi_option__option', flat=True).distinct())
        elif isinstance(attr, AttributeOption):
            return attr.option
        else:
            return attr

    def get_product_attributes(self, product):
        data = {}
        for attr in product.attr:
            data[attr.attribute.code] = self.get_attribute_data(product, attr.attribute.code)

        return data

    def prepare_variants(self, product):
        variant_data = []
        if product.is_parent:
            for child in product.children.all():
                variant_data.append(self.get_product_attributes(child))
        else:
            variant_data.append(self.get_product_attributes(product))

        return variant_data

    @staticmethod
    def sanitize_description(description):
        return ' '.join(strip_tags(description).strip().split())

    def prepare_description(self, product):
        return self.sanitize_description(product.description)

    def prepare_stock(self, product):
        if product.is_standalone and not product.has_stockrecords:
            # For parent products... we don't currently handle this case
            return None

        stocks = []

        if product.is_parent:
            stockrecords = StockRecord.objects.filter(product__in=product.children.all())
        else:
            stockrecords = product.stockrecords.all()

        for stockrecord in stockrecords:
            stocks.append(self.get_stockrecord_data(stockrecord))

        return stocks

    def prepare_categories(self, product):
        categories = product.categories.all()
        all_cats = set()
        for cat in categories:
            all_cats.add(cat.pk)
            all_cats.update(set(cat.get_ancestors().values_list('id', flat=True)))
        return list(all_cats)

    def prepare_score(self, product):
        months_to_run = getattr(settings, 'MONTHS_TO_RUN_ANALYTICS', 3)
        orders_above_date = timezone.now() - relativedelta(months=months_to_run)

        return Line.objects.filter(product=product, order__date_placed__gte=orders_above_date).count()

    def get_stockrecord_data(self, stockrecord):
        # Exclude stock records that have no price
        if not stockrecord.price_excl_tax:
            return None

        # Partner can be missing when loading data from fixtures
        try:
            partner = stockrecord.partner.pk
        except ObjectDoesNotExist:
            return None

        return {
            'partner': partner,
            'currency': stockrecord.price_currency,
            'price': stockrecord.price_excl_tax,
            'num_in_stock': stockrecord.net_stock_level,
            'sku': stockrecord.partner_sku
        }

    class Meta:
        doc_type = 'product'
        index = settings.OSCAR_SEARCH['INDEX_NAME']
        model = Product
        mapping = product_mapping
        dynamic = MetaField('strict')
