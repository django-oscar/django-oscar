from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.module_loading import import_string

from oscar.core.loading import get_class, get_model

from . import filter
from oscar.apps.search import forms
from oscar.apps.search.base import BaseSearchHandler
from . import forms

Category = get_model('catalogue', 'Category')


def get_product_search_handler_class():
    """
    Import and return the search handler class.
    """
    # Use get_class to ensure overridability
    return import_string(settings.OSCAR_PRODUCT_SEARCH_HANDLER)


class ProductSearchHandler(BaseSearchHandler):
    """
    Category search handler. Must expose a handful of methods that Oscar is
    expecting. Refer to oscar.apps.search.search_handlers for more information.
    """

    form_class = forms.CatalogueSearchForm
    query = get_class('catalogue.query', 'ProductSearch')

    def __init__(self, request_data, full_path, categories=None, **kwargs):
        super(ProductSearchHandler, self).__init__(request_data, full_path, **kwargs)
        self.categories = categories
        self.currency = kwargs.pop('currency', settings.OSCAR_DEFAULT_CURRENCY)

        # Allow a custom default sort order for the category views
        request_data = request_data.copy()
        default_sort = settings.OSCAR_SEARCH.get('DEFAULT_CATEGORY_SORT_BY')
        if default_sort and not request_data.get('sort_by'):
            request_data['sort_by'] = default_sort

        # Triggers the search. All exceptions (404, Invalid Page) must be raised
        # at init time from inside one of these methods.
        self.results = self.get_results(request_data)
        self.context = self.prepare_context(self.results)

    # Search related methods

    def get_filters(self, form_data):
        filters = {}

        if self.categories:
            form_data['category'] = self.categories[-1].pk

        if form_data.get('category'):
            filters['categories'] = {
                'type': 'term',
                'params': {'categories': int(form_data.get('category'))}
            }

        price_min = form_data.get('price_min')
        price_max = form_data.get('price_max')
        if price_min is not None:
            price_params = {
                'gte': float(price_min)
            }
            if price_max is not None:
                price_params['lte'] = float(price_max)

            # Does your head hurt making sense of this?
            filters['price'] = {
                'type': 'nested',
                'params': {
                    'path': 'stock',
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'range': {'stock.price': price_params}
                                },
                                {
                                    'match': {'stock.currency': self.currency}
                                },
                            ]
                        }
                    }
                }
            }

        if settings.OSCAR_SEARCH.get('HIDE_OOS_FROM_CATEGORY_VIEW'):
            filters['num_in_stock'] = {
                'type': 'nested',
                'params': {
                    'path': 'stock',
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'range': {'stock.price': {'gt': 0}}
                                },
                                {
                                    'match': {'stock.currency': self.currency}
                                },
                            ]
                        }
                    }
                }
            }

        # Filter for the selected currency
        filters['currency'] = {
            'type': 'nested',
            'params': {
                'path': 'stock',
                'query': {
                    'match': {'stock.currency': self.currency}
                }
            }
        }

        return filters

    def get_category_tree(self):
        if self.categories:
            return filter.build_category_tree(
                request_url=self.full_path,
                category=self.categories[-1].pk,
                agg=self.results['other_aggs']['category'],
                use_cat_url=True
            )
        else:
            return filter.build_category_tree(
                request_url=self.full_path,
                category=self.request_data.get('category'),
                agg=self.results['other_aggs']['category']
            )

    def get_search_kwargs(self, search_form, page_no=1):
        kwargs = super(ProductSearchHandler, self).get_search_kwargs(search_form, page_no)
        kwargs['currency'] = self.currency
        return kwargs

    def get_search_context_data(self, context_object_name=None):
        """
        Oscar's category view expects this method to return the template context
        """
        return self.context

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

            if 'category' in results['other_aggs']:
                context['categories'] = self.get_category_tree()

            if results['price_ranges']:
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


class OnSaleSearchHandler(ProductSearchHandler):

    def get_filters(self, form_data):
        filters = super(OnSaleSearchHandler, self).get_filters(form_data)
        filters['on_sale'] = {
            'type': 'nested',
            'params': {
                'path': 'stock',
                'query': {
                    'bool': {
                        'must': [
                            {
                                'match': {'stock.on_sale': True}
                            },
                            {
                                'match': {'stock.currency': self.currency}
                            },
                        ]
                    }
                }
            }
        }

        return filters


class ManufacturerSearchHandler(ProductSearchHandler):

    def __init__(self, manufacturer, *args, **kwargs):
        self.manufacturer = manufacturer
        super(ManufacturerSearchHandler, self).__init__(*args, **kwargs)

    def get_filters(self, form_data):
        filters = super(ManufacturerSearchHandler, self).get_filters(form_data)
        filters['manufacturer'] = {
            'type': 'term',
            'params': {'manufacturer.keyword': self.manufacturer.name}
        }
        return filters