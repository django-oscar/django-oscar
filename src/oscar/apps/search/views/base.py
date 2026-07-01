from django.conf import settings

from haystack.generic_views import FacetedSearchView as BaseFacetedSearchView

from oscar.core.loading import get_class

FacetMunger = get_class("search.facets", "FacetMunger")
base_sqs = get_class("search.facets", "base_sqs")


class BaseSearchView(BaseFacetedSearchView):
    facet_fields = settings.OSCAR_SEARCH_FACETS["fields"].keys()
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

    def get_queryset(self):
        return base_sqs()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        form = context[self.form_name]

        # Show suggestion no matter what.  Haystack 2.1 only shows a suggestion
        # if there are some results, which seems a bit weird to me.
        if self.queryset.query.backend.include_spelling:
            # Note, this triggers an extra call to the search backend
            suggestion = form.get_suggestion()
            if suggestion != context["query"]:
                context["suggestion"] = suggestion

        # Convert facet data into a more useful data structure
        if "fields" in context["facets"]:
            munger = FacetMunger(
                self.request.get_full_path(),
                form.selected_multi_facets,
                self.queryset.facet_counts(),
                query_type=type(self.queryset.query),
            )
            context["facet_data"] = munger.facet_data()
            has_facets = any(
                [len(data["results"]) for data in context["facet_data"].values()]
            )
            context["has_facets"] = has_facets

        context["selected_facets"] = form.selected_facets
        context[self.page_kwarg] = context["page_obj"]

        return context
