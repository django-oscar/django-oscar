"""
Overrides of oscarapi.views.product, loaded through OSCARAPI_OVERRIDE_MODULES.
"""
from oscar.core.loading import get_class, get_model
from oscarapi.views import product as core_views

from apps.api.mobile_serializers import (
    MobileCategorySerializer,
    MobileProductSerializer,
)

Selector = get_class("partner.strategy", "Selector")
Category = get_model("catalogue", "Category")
Product = get_model("catalogue", "Product")


class MobileStrategyMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        request = self.request
        context["strategy"] = Selector().strategy(request=request, user=request.user)
        return context


class ProductList(MobileStrategyMixin, core_views.ProductList):
    """
    Browsable products with price and availability inlined.

    Supports ``?category=<id>`` (the category and its descendants) on top of
    the core ``?structure=`` filter.
    """

    queryset = Product.objects.browsable().prefetch_related(
        "images", "categories", "stockrecords"
    )
    serializer_class = MobileProductSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category_id = self.request.query_params.get("category")
        if category_id:
            try:
                category = Category.objects.get(pk=int(category_id))
            except (ValueError, Category.DoesNotExist):
                return qs.none()
            qs = qs.filter(
                categories__in=category.get_descendants_and_self()
            ).distinct()
        return qs


class ProductDetail(MobileStrategyMixin, core_views.ProductDetail):
    queryset = Product.objects.browsable()
    serializer_class = MobileProductSerializer


class CategoryList(core_views.CategoryList):
    """
    Public categories with ``parent_id`` and ``has_children``.

    ``?parent=<id>`` lists the children of a category (``0`` or missing: root
    categories); the core breadcrumbs URL keeps working.
    """

    serializer_class = MobileCategorySerializer

    def get_queryset(self):
        parent_id = self.request.query_params.get("parent")
        if parent_id and parent_id != "0" and "breadcrumbs" not in self.kwargs:
            try:
                qs = Category.objects.get(pk=int(parent_id)).get_children()
            except (ValueError, Category.DoesNotExist):
                return Category.objects.none()
        else:
            qs = super().get_queryset()
        return qs.filter(is_public=True)
