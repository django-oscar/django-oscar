from django.core.paginator import InvalidPage, Paginator
from django.utils.translation import ugettext_lazy as _
from haystack import connections

from oscar.core.loading import get_class

from . import facets

FacetMunger = get_class('search.facets', 'FacetMunger')


class SearchHandler(object):
    """
    A class that is concerned with performing a search and paginating the
    results. The search is triggered upon initialisation (mainly to have a
    predictable point to process any errors).  Search results are cached, so
    they can be accessed multiple times without incurring any overhead.

    The raison d'etre for this third way to interface with Haystack is
    two-fold. The Haystack search form doesn't do enough for our needs, and
    basing a view off a Haystack search view is unnecessarily invasive.
    Furthermore, using our own search handler means it is easy to swap
    out Haystack, which has been considered before.

    Usage:

        handler = SearchHandler(request.GET, request.get_full_path)
        found_objects = handler.get_paginated_objects()
        context = handler.get_search_context_data()

    Error handling:

        You need to catch an InvalidPage exception which gets thrown when an
        invalid page number is supplied.
    """

    form_class = None
    model_whitelist = None
    paginate_by = None
    paginator_class = Paginator
    page_kwarg = 'page'

    def __init__(self, request_data, full_path):
        self.full_path = full_path
        self.request_data = request_data

        # Triggers the search.
        search_queryset = self.get_search_queryset()
        self.search_form = self.get_search_form(
            request_data, search_queryset)
        self.results = self.get_search_results(self.search_form)
        # If below raises an UnicodeDecodeError, you're running pysolr < 3.2
        # with Solr 4.
        self.paginator, self.page = self.paginate_queryset(
            self.results, request_data)

    # Search related methods

    def get_search_results(self, search_form):
        """
        Perform the actual search using Haystack's search form. Returns
        a SearchQuerySet. The SQS is empty if the form is invalid.
        """
        return search_form.search()

    def get_search_form(self, request_data, search_queryset):
        """
        Return a bound version of Haystack's search form.
        """
        kwargs = {
            'data': request_data,
            'selected_facets': request_data.getlist("selected_facets"),
            'searchqueryset': search_queryset
        }
        return self.form_class(**kwargs)

    def get_search_queryset(self):
        """
        Returns the search queryset that is used as a base for the search.
        """
        sqs = facets.base_sqs()
        if self.model_whitelist:
            # Limit queryset to specified list of models
            sqs = sqs.models(*self.model_whitelist)
        return sqs

    # Pagination related methods

    def paginate_queryset(self, queryset, request_data):
        """
        Paginate the search results. This is a simplified version of
        Django's MultipleObjectMixin.paginate_queryset
        """
        paginator = self.get_paginator(queryset)
        page_kwarg = self.page_kwarg
        page = request_data.get(page_kwarg, 1)
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise InvalidPage(_(
                    "Page is not 'last', nor can it be converted to an int."))
        # This can also raise an InvalidPage exception.
        return paginator, paginator.page(page_number)

    def get_paginator(self, queryset):
        """
        Return a paginator. Override this to set settings like orphans,
        allow_empty, etc.
        """
        return self.paginator_class(queryset, self.paginate_by)

    # Accessing the search results and meta data

    def bulk_fetch_results(self, paginated_results):
        """
        This method gets paginated search results and returns a list of Django
        objects in the same order.

        It preserves the order without doing any ordering in Python, even
        when more than one Django model are returned in the search results. It
        also uses the same queryset that was used to populate the search
        queryset, so any select_related/prefetch_related optimisations are
        in effect.

        It is heavily based on Haystack's SearchQuerySet.post_process_results,
        but works on the paginated results instead of all of them.
        """
        objects = []

        models_pks = loaded_objects = {}
        for result in paginated_results:
            models_pks.setdefault(result.model, []).append(result.pk)

        search_backend_alias = self.results.query.backend.connection_alias
        for model in models_pks:
            ui = connections[search_backend_alias].get_unified_index()
            index = ui.get_index(model)
            queryset = index.read_queryset(using=search_backend_alias)
            loaded_objects[model] = queryset.in_bulk(models_pks[model])

        for result in paginated_results:
            model_objects = loaded_objects.get(result.model, {})
            try:
                result._object = model_objects[int(result.pk)]
            except KeyError:
                # The object was either deleted since we indexed or should
                # be ignored; fail silently.
                pass
            else:
                objects.append(result._object)

        return objects

    def get_paginated_objects(self):
        """
        Return a paginated list of Django model instances. The call is cached.
        """
        if hasattr(self, '_objects'):
            return self._objects
        else:
            paginated_results = self.page.object_list
            self._objects = self.bulk_fetch_results(paginated_results)
        return self._objects

    def get_facet_munger(self):
        return FacetMunger(
            self.full_path,
            self.search_form.selected_multi_facets,
            self.results.facet_counts())

    def get_search_context_data(self, context_object_name=None):
        """
        Return metadata about the search in a dictionary useful to populate
        template contexts. If you pass in a context_object_name, the dictionary
        will also contain the actual list of found objects.

        The expected usage is to call this function in your view's
        get_context_data:

            search_context = self.search_handler.get_search_context_data(
                self.context_object_name)
            context.update(search_context)
            return context

        """

        # Use the FacetMunger to convert Haystack's awkward facet data into
        # something the templates can use.
        # Note that the FacetMunger accesses object_list (unpaginated results),
        # whereas we use the paginated search results to populate the context
        # with products
        munger = self.get_facet_munger()
        facet_data = munger.facet_data()
        has_facets = any([data['results'] for data in facet_data.values()])

        context = {
            'facet_data': facet_data,
            'has_facets': has_facets,
            # This is a serious code smell; we just pass through the selected
            # facets data to the view again, and the template adds those
            # as fields to the form. This hack ensures that facets stay
            # selected when changing relevancy.
            'selected_facets': self.request_data.getlist('selected_facets'),
            'form': self.search_form,
            'paginator': self.paginator,
            'page_obj': self.page,
        }

        # It's a pretty common pattern to want the actual results in the
        # context, so pass them in if context_object_name is set.
        if context_object_name is not None:
            context[context_object_name] = self.get_paginated_objects()

        return context
