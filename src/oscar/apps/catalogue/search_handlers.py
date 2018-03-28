from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_string

from oscar.apps.search.search_handlers import BaseSearchHandler
from oscar.core.loading import get_class, get_model

from . import filter
from . import forms

Category = get_model('catalogue', 'Category')
PriceRangeSearch = get_class('catalogue.search', 'PriceRangeSearch')


def get_product_search_handler_class(search=True):
    if search and settings.OSCAR_PRODUCT_SEARCH_HANDLER is not None:
        return import_string(settings.OSCAR_PRODUCT_SEARCH_HANDLER)
    elif settings.OSCAR_PRODUCT_BROWSE_SEARCH_HANDLER is not None:
        return import_string(settings.OSCAR_PRODUCT_BROWSE_SEARCH_HANDLER)
    else:
        return get_class('catalogue.search_handlers', 'ProductSearchHandler')


class ProductSearchHandler(BaseSearchHandler):
    """
    Category search handler. Must expose a handful of methods that Oscar is
    expecting. Refer to oscar.apps.search.search_handlers for more information.
    """

    form_class = forms.CatalogueSearchForm
    query = get_class('catalogue.search', 'ProductSearch')
    applied_filters = ['category', 'price', 'num_in_stock', 'currency']

    def __init__(self, request_data, full_path, categories=None, **kwargs):
        self.categories = categories
        self.currency = kwargs.pop('currency', settings.OSCAR_DEFAULT_CURRENCY)

        super(ProductSearchHandler, self).__init__(request_data, full_path, **kwargs)

    def get_category_filters(self, form_data):
        if self.categories:
            form_data['category'] = self.categories[-1].pk

        category = form_data.get('category')
        if category:
            return {
                'type': 'term',
                'params': {'categories': int(category)}
            }

    def get_price_filters(self, form_data):
        price_min = form_data.get('price_min')
        price_max = form_data.get('price_max')
        if price_min is not None:
            price_params = {
                'gte': float(price_min)
            }
            if price_max is not None:
                price_params['lte'] = float(price_max)

            return {
                'type': 'nested',
                'params': {
                    'path': 'stock',
                    'query': {
                        'range': {
                            'stock.price': price_params
                        }
                    }
                }
            }

    def get_num_in_stock_filters(self, form_data):
        if settings.OSCAR_SEARCH.get('HIDE_OOS_FROM_CATEGORY_VIEW'):
            return {
                'type': 'nested',
                'params': {
                    'path': 'stock',
                    'query': {
                        'range': {
                            'stock.num_in_stock': {'gt': 0}
                        }
                    }
                }
            }

    def get_currency_filters(self, form_data):
        return {
            'type': 'nested',
            'params': {
                'path': 'stock',
                'query': {
                    'match': {'stock.currency': self.currency}
                }
            }
        }

    def get_filters(self, form_data):
        filters = {}

        for _filter in self.applied_filters:
            filter_method = getattr(self, 'get_{}_filters'.format(_filter), None)
            if filter_method:
                filter_data = filter_method(form_data)
                if filter_data:
                    filters[_filter] = filter_data

        return filters

    def get_category_tree(self, category_agg):
        if self.categories:
            return filter.build_category_tree(
                request_url=self.full_path,
                category=self.categories[-1].pk,
                agg=category_agg,
                use_cat_url=True
            )
        else:
            return filter.build_category_tree(
                request_url=self.full_path,
                category=self.request_data.get('category'),
                agg=category_agg
            )

    def get_search_kwargs(self, search_form, page_number=1):
        kwargs = super(ProductSearchHandler, self).get_search_kwargs(search_form, page_number)
        kwargs['currency'] = self.currency
        return kwargs

    def get_search_context_data(self, context_object_name=None):
        """
        Oscar's category view expects this method to return the template context
        """
        return self.context

    def get_results(self, request_data):
        results = super(ProductSearchHandler, self).get_results(request_data)

        search_kwargs = self.get_search_kwargs(self.form)
        if settings.OSCAR_SEARCH.get('SHOW_PRICE_RANGE_FACET', False):
            results['price_ranges'] = PriceRangeSearch(**search_kwargs).get_price_ranges()

        return results

    def prepare_context(self, results):
        context = super(ProductSearchHandler, self).prepare_context(results)

        if results is not None:
            # Filters
            if self.request_data.get('category'):
                try:
                    cat_id = int(self.request_data.get('category'))
                except ValueError:
                    raise Http404()
                context['category'] = get_object_or_404(Category, pk=cat_id)

            if 'category' in results.get('other_aggs', {}):
                context['categories'] = self.get_category_tree(results['other_aggs']['category'])

            if 'price_ranges' in results and results['price_ranges']:
                context['price_ranges'] = filter.build_price_ranges(
                    price_ranges=results['price_ranges'],
                    currency=self.currency,
                    request_url=self.full_path
                )
            elif self.form.cleaned_data.get('price_min') is not None:
                context['clear_price_url'] = filter.clear_price_from_url(self.full_path)
                context['selected_price_range'] = filter.price_display_name(
                    self.form.cleaned_data.get('price_min'),
                    self.form.cleaned_data.get('price_max'),
                    self.currency
                )

        return context
