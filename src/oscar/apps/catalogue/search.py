import math

from django.conf import settings
from elasticsearch_dsl import TermsFacet, Q

from oscar.apps.catalogue.documents import ProductDocument
from oscar.apps.search.search import BaseSearch, BaseAutoSuggestSearch

from oscar.apps.search import utils


class ProductSearch(BaseSearch):

    document = ProductDocument
    settings_key = 'PRODUCTS'

    def __init__(self, currency=None, category_id=None, *args, **kwargs):
        self.currency = currency

        search_filters = kwargs.get('search_filters') or {}
        if category_id and 'category' not in search_filters:
            search_filters['category'] = {
                'type': 'term',
                'params': {'categories': int(category_id)}
            }

        kwargs['search_filters'] = search_filters

        super(ProductSearch, self).__init__(*args, **kwargs)

    def get_extra_facets(self):
        return {
            'category': TermsFacet(field='categories', size=100000)
        }

    def suggest(self, search):
        if self._query:
            search = search.suggest('suggestions', self._query,
                                    phrase={'field': 'raw_title', 'size': 1, 'max_errors': 2.0})

        return search

    def build_search(self):
        search = super(ProductSearch, self).build_search()
        search = self.suggest(search)
        search = self.filter_in_stock(search)
        return search

    def filter_in_stock(self, search):
        products_have_stockrecords = settings.OSCAR_PRODUCTS_HAVE_STOCKRECORDS
        filter_in_stock = settings.OSCAR_SEARCH[self.settings_key].get('filter_in_stock', False)

        if products_have_stockrecords and filter_in_stock:
            query = Q('range', stock__num_in_stock={'gt': 0})
            if self.currency:
                query = query & Q('match', stock__currency=self.currency)

            search = search.filter('nested',
                                   path='stock',
                                   query=query)

        return search


class PriceRangeSearch(ProductSearch):

    source_fields = ['stock']

    # change signature to make currency compulsory
    def __init__(self, currency, *args, **kwargs):
        kwargs['currency'] = currency
        kwargs['max_results'] = 10000
        super(PriceRangeSearch, self).__init__(*args, **kwargs)

    def aggregate(self, search):
        pass

    def sort(self, search):
        search = search.sort({
            'stock.price': {
                'order': 'asc',
                'mode': 'min',
                'nested_path': 'stock',
                'nested_filter': {
                    'match': {'stock.currency': self.currency}
                }
            }
        })

        return search

    def extract_prices(self, results):
        """

        :param results: Search results from Elastic search
        :return: List of prices
        """
        prices = []
        for p in results:
            if 'stock' in p:
                # Take the first stock record we find that has the right currency
                # TODO is there any way to filter these in ES?
                stocks = [x for x in p['stock'] if x['currency'] == self.currency]
                if stocks:
                    prices.append(stocks[0]['price'])

        return prices

    def parse_price_ranges_results(self, results):
        prices = self.extract_prices(results)

        price_count = len(prices)
        if price_count < 10:
            return

        n_groups = settings.OSCAR_SEARCH.get('PRICE_FACET_COUNT', 5)
        group_size = int(math.ceil(price_count / n_groups))
        chunks = utils.chunks(prices, group_size)

        return utils.get_auto_ranges(chunks)

    def get_price_ranges(self):
        results = self.execute()
        return self.parse_price_ranges_results(results)


class RelatedProductSearch(ProductSearch):

    compare_fields = settings.OSCAR_SEARCH.get('RELATED_PRODUCT_FIELDS', ['title', 'description'])
    settings_key = 'RELATED_PRODUCTS'

    def __init__(self, product_ids, *args, **kwargs):
        self.product_ids = product_ids

        # set max_results default to 5
        kwargs['max_results'] = kwargs.get('max_results') or 5

        super(RelatedProductSearch, self).__init__(*args, **kwargs)

    def build_search(self):
        search = self.search()
        search = search.query(
            'more_like_this',
            fields=self.compare_fields,
            ids=self.product_ids
        )

        search = self.search_filters(search)
        search = self.filter_in_stock(search)
        search = self.limit_count(search)
        return search

    def get_related_products(self):
        results = self.execute()
        return self.obj_list_from_results(results)


class CatalogueAutoSuggestSearch(ProductSearch, BaseAutoSuggestSearch):

    source_fields = ['title', 'url']


class TopProductsSearch(ProductSearch):

    settings_key = 'TOP_PRODUCTS'

    def __init__(self, *args, **kwargs):
        kwargs['sort'] = '-score'
        kwargs['max_results'] = kwargs.get('max_results') or 10
        super(TopProductsSearch, self).__init__(*args, **kwargs)

    def get_top_products(self):
        results = self.execute()
        return self.obj_list_from_results(results)
