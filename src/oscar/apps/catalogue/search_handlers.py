from django.conf import settings
from django.utils.module_loading import import_string
from django.views.generic.list import MultipleObjectMixin

from oscar.core.loading import get_class, get_model

BrowseCategoryForm = get_class('search.forms', 'BrowseCategoryForm')
SearchHandler = get_class('search.search_handlers', 'SearchHandler')
is_solr_supported = get_class('search.features', 'is_solr_supported')
is_elasticsearch_supported = get_class('search.features', 'is_elasticsearch_supported')
Product = get_model('catalogue', 'Product')


def get_product_search_handler_class():
    """
    Determine the search handler to use.

    Currently only Solr is supported as a search backend, so it falls
    back to rudimentary category browsing if that isn't enabled.
    """
    # Use get_class to ensure overridability
    if settings.OSCAR_PRODUCT_SEARCH_HANDLER is not None:
        return import_string(settings.OSCAR_PRODUCT_SEARCH_HANDLER)
    if is_solr_supported():
        return get_class('catalogue.search_handlers', 'SolrProductSearchHandler')
    elif is_elasticsearch_supported():
        return get_class(
            'catalogue.search_handlers', 'ESProductSearchHandler',
        )
    else:
        return get_class(
            'catalogue.search_handlers', 'SimpleProductSearchHandler')


class SolrProductSearchHandler(SearchHandler):
    """
    Search handler specialised for searching products.  Comes with optional
    category filtering. To be used with a Solr search backend.
    """
    form_class = BrowseCategoryForm
    model_whitelist = [Product]
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

    def __init__(self, request_data, full_path, categories=None):
        self.categories = categories
        super(SolrProductSearchHandler, self).__init__(request_data, full_path)

    def get_search_queryset(self):
        sqs = super(SolrProductSearchHandler, self).get_search_queryset()
        if self.categories:
            # We use 'narrow' API to ensure Solr's 'fq' filtering is used as
            # opposed to filtering using 'q'.
            pattern = ' OR '.join([
                '"%s"' % sqs.query.clean(c.full_name) for c in self.categories])
            sqs = sqs.narrow('category_exact:(%s)' % pattern)
        return sqs


class ESProductSearchHandler(SearchHandler):
    """
    Search handler specialised for searching products.  Comes with optional
    category filtering. To be used with an ElasticSearch search backend.
    """
    form_class = BrowseCategoryForm
    model_whitelist = [Product]
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

    def __init__(self, request_data, full_path, categories=None):
        self.categories = categories
        super(ESProductSearchHandler, self).__init__(request_data, full_path)

    def get_search_queryset(self):
        sqs = super(ESProductSearchHandler, self).get_search_queryset()
        if self.categories:
            for category in self.categories:
                sqs = sqs.filter_or(category=category.full_name)
        return sqs


class SimpleProductSearchHandler(MultipleObjectMixin):
    """
    A basic implementation of the full-featured SearchHandler that has no
    faceting support, but doesn't require a Haystack backend. It only
    supports category browsing.

    Note that is meant as a replacement search handler and not as a view
    mixin; the mixin just does most of what we need it to do.
    """
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

    def __init__(self, request_data, full_path, categories=None):
        self.categories = categories
        self.kwargs = {'page': request_data.get('page', 1)}
        self.object_list = self.get_queryset()

    def get_queryset(self):
        qs = Product.browsable.base_queryset()
        if self.categories:
            qs = qs.filter(categories__in=self.categories).distinct()
        return qs

    def get_search_context_data(self, context_object_name):
        # Set the context_object_name instance property as it's needed
        # internally by MultipleObjectMixin
        self.context_object_name = context_object_name
        context = self.get_context_data(object_list=self.object_list)
        context[context_object_name] = context['page_obj'].object_list
        return context
