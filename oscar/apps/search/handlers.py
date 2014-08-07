from django.core.paginator import Paginator, InvalidPage
from django.utils.translation import ugettext_lazy as _
from haystack import connections

from oscar.core.loading import get_class
from . import facets


FacetMunger = get_class('search.facets', 'FacetMunger')


class SearchHandler(object):
    """
    A class that is concerned with performing a search and paginate the
    results. The search is triggered upon initialisation (mainly to have a
    predictable point to process any errors).
    Search results are cached, so they can be accessed multiple times without
    incurring any overhead.

    The raison d'etre for this third way to interface with Haystack is that
    two-fold. The Haystack search form doesn't do enough for our needs, and
    basing a view off a Haystack search view is unnecessarily invasive.
    Furthermore, using our own search handler does mean it is easy to swap
    out Haystack, which has been considered before.

    Usage:

        handler = SearchHandler(request.GET, request.get_full_path)
        found_objects = handler.get_paginated_objects()
        context = handler.get_search_context_data()

    Error handling:
        You need to catch a ValueError which gets thrown when an invalid
        page number is supplied.
    """

    form_class = None
    model_whitelist = None
    paginate_by = None
    paginator_class = Paginator
    page_kwarg = 'page'

    def __init__(self, request_data, full_path):
        self.request_data = request_data
        self.full_path = full_path

        # trigger the search
        search_results = self.get_search_results()
        self.paginator, self.page = self.paginate_queryset(search_results)

    # Search related methods

    def get_search_results(self):
        """
        Performs the actual search, using Haystack's search form.
        """
        if not hasattr(self, '_results'):
            self.search_form = self.get_search_form()
            # Returns empty query set if form is invalid.
            self._results = self.search_form.search()
        return self._results

    def get_search_form(self):
        """
        Returns a bound version of Haystack's search form.
        """
        kwargs = {
            'data': self.request_data,
            'selected_facets': self.request_data.getlist("selected_facets"),
            'searchqueryset': self.get_search_queryset()
        }
        return self.form_class(**kwargs)

    def get_search_queryset(self):
        sqs = facets.base_sqs()
        if self.model_whitelist:
            # limit queryset to specified list of models
            sqs = sqs.models(*self.model_whitelist)
        return sqs

    # Pagination related methods

    def paginate_queryset(self, queryset):
        """
        Paginate the search results. This is a simplified version of
        Django's MultipleObjectMixin.paginate_queryset
        """
        paginator = self.get_paginator(queryset)
        page_kwarg = self.page_kwarg
        page = self.request_data.get(page_kwarg, 1)
        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                raise ValueError(_(
                    "Page is not 'last', nor can it be converted to an int."))
        try:
            page = paginator.page(page_number)
            return paginator, page
        except InvalidPage as e:
            raise ValueError(
                _('Invalid page (%(page_number)s): %(message)s') % {
                    'page_number': page_number,
                    'message': str(e)
                })

    def get_paginator(self, queryset):
        """
        Returns a paginator. Override this to set settings like
        orphans, allow_empty, etc.
        """
        return self.paginator_class(queryset, self.paginate_by)

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

        search_backend_alias = self._results.query.backend.connection_alias
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

    # Accessing the search results and meta data

    def get_paginated_objects(self):
        """
        Returns a paginated list of Django model instances.
        """
        if not hasattr(self, '_object_list'):
            paginated_results = self.page.object_list
            self._object_list = self.bulk_fetch_results(paginated_results)
        return self._object_list

    def get_search_context_data(self, context_object_name=None):
        """
        Returns meta data about the search in a dictionary useful to populate
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
        munger = FacetMunger(
            self.full_path,
            self.search_form.selected_multi_facets,
            self.get_search_results().facet_counts())
        facet_data = munger.facet_data()
        has_facets = any([data['results'] for data in facet_data.values()])

        context = {
            'facet_data': facet_data,
            'has_facets': has_facets,
            'form': self.search_form,
            'paginator': self.paginator,
            'page_obj': self.page,
        }

        # It's a pretty common pattern to want the actual results in the
        # context, so pass them in if context_object_name is set.
        if context_object_name is not None:
            context[context_object_name] = self.get_paginated_objects()

        return context
