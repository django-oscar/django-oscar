from django.conf import settings

from haystack.generic_views import FacetedSearchView as BaseFacetedSearchView

from oscar.core.loading import get_class, get_model

FacetMunger = get_class("search.facets", "FacetMunger")
Product = get_model("catalogue", "Product")


class BaseSearchView(BaseFacetedSearchView):
    facet_fields = settings.OSCAR_SEARCH_FACETS["fields"].keys()
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Show suggestion no matter what.  Haystack 2.1 only shows a suggestion
        # if there are some results, which seems a bit weird to me.
        if self.queryset.query.backend.include_spelling:
            # Note, this triggers an extra call to the search backend
            suggestion = context["form"].get_suggestion()
            if suggestion != context["query"]:
                context["suggestion"] = suggestion

        # Convert facet data into a more useful data structure
        if "fields" in context["facets"]:
            munger = FacetMunger(
                self.request.get_full_path(),
                context[self.form_name].selected_multi_facets,
                self.queryset.facet_counts(),
            )
            context["facet_data"] = munger.facet_data()
            has_facets = any(
                [len(data["results"]) for data in context["facet_data"].values()]
            )
            context["has_facets"] = has_facets

        return context
