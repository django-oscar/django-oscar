from haystack import indexes
from django.conf import settings

from oscar.core.loading import get_model, get_class

# Load default strategy (without a user/request)
Selector = get_class('partner.strategy', 'Selector')
strategy = Selector().strategy()


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    # Search text
    text = indexes.EdgeNgramField(
        document=True, use_template=True,
        template_name='oscar/search/indexes/product/item_text.txt')

    upc = indexes.CharField(model_attr="upc", null=True)
    title = indexes.EdgeNgramField(model_attr='title', null=True)

    # Fields for faceting
    product_class = indexes.CharField(null=True, faceted=True)
    category = indexes.MultiValueField(null=True, faceted=True)
    price = indexes.DecimalField(null=True, faceted=True)
    num_in_stock = indexes.IntegerField(null=True, faceted=True)
    rating = indexes.IntegerField(null=True, faceted=True)

    # Fields for boosting
    score = indexes.FloatField()

    # Spelling suggestions
    suggestions = indexes.FacetCharField()

    date_created = indexes.DateTimeField(model_attr='date_created')
    date_updated = indexes.DateTimeField(model_attr='date_updated')

    def get_model(self):
        return get_model('catalogue', 'Product')

    def index_queryset(self, using=None):
        # Only index browsable products (not each individual variant)
        return self.get_model().browsable.order_by('-date_updated')

    def read_queryset(self, using=None):
        return self.get_model().browsable.base_queryset()

    def prepare_product_class(self, obj):
        return obj.get_product_class().name

    def prepare_category(self, obj):
        categories = obj.categories.all()
        if len(categories) > 0:
            return [category.full_name for category in categories]

    def prepare_rating(self, obj):
        if obj.rating is not None:
            return int(obj.rating)

    # Pricing and stock is tricky as it can vary per customer.  However, the
    # most common case is for customers to see the same prices and stock levels
    # and so we implement that case here.

    def prepare_price(self, obj):
        result = None
        if obj.is_group:
            result = strategy.fetch_for_group(obj)
        elif obj.has_stockrecords:
            result = strategy.fetch_for_product(obj)

        if result:
            if result.price.is_tax_known:
                return result.price.incl_tax
            return result.price.excl_tax

    def prepare_num_in_stock(self, obj):
        result = None
        if obj.is_group:
            # Don't return a stock level for group products
            return None
        elif obj.has_stockrecords:
            result = strategy.fetch_for_product(obj)
            return result.stockrecord.net_stock_level

    def prepare_score(self, obj):
        return obj.score

    def prepare(self, obj):
        prepared_data = super(ProductIndex, self).prepare(obj)

        # We use Haystack's dynamic fields to ensure that the title field used
        # for sorting is of type "string'.
        if 'solr' in settings.HAYSTACK_CONNECTIONS['default']['ENGINE']:
            prepared_data['title_s'] = prepared_data['title']

        # Use title to for spelling suggestions
        prepared_data['suggestions'] = prepared_data['text']

        return prepared_data

    def get_updated_field(self):
        """
        Used to specify the field used to determine if an object has been
        updated

        Can be used to filter the query set when updating the index
        """
        return 'date_updated'
