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
