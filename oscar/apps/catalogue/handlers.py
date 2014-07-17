from django.conf import settings
from django.views.generic.list import MultipleObjectMixin
from oscar.core.loading import get_class, get_model


BrowseCategoryForm = get_class('search.forms', 'BrowseCategoryForm')
SearchHandler = get_class('search.handlers', 'SearchHandler')
Product = get_model('catalogue', 'Product')


class ProductSearchHandler(SearchHandler):
    """
    A search handler that is specialised for searching Oscar products.
    Comes with automatic category filtering.
    """
    form_class = BrowseCategoryForm
    model_whitelist = [Product]
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

    def __init__(self, categories, request_data, full_path):
        self.categories = categories
        super(ProductSearchHandler, self).__init__(request_data, full_path)

    def get_search_queryset(self):
        sqs = super(ProductSearchHandler, self).get_search_queryset()
        if self.categories:
            # We use 'narrow' API to ensure Solr's 'fq' filtering is used as
            # opposed to filtering using 'q'.
            pattern = ' OR '.join([
                '"%s"' % c.full_name for c in self.categories])
            sqs = sqs.narrow('category_exact:(%s)' % pattern)
        return sqs


class SimpleProductSearchHandler(MultipleObjectMixin):
    """
    A basic implementation of the full-featured SearchHandler that has no
    faceting support, but doesn't require a Haystack backend. It only
    supports category browsing.
    """
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

    def __init__(self, categories, request_data, *args, **kwargs):
        self.categories = categories
        self.kwargs = {'page': request_data.get('page', 1)}
        self.object_list = self.get_queryset()

    def get_queryset(self):
        qs = Product.browsable.base_queryset()
        if self.categories:
            qs = qs.filter(categories__in=self.categories).distinct()
        return qs

    def get_search_context_data(self, context_object_name):
        self.context_object_name = context_object_name
        context = self.get_context_data(object_list=self.object_list)
        context[context_object_name] = context['page_obj'].object_list
        return context
