"""
Overrides of oscarapi.views.product, loaded through OSCARAPI_OVERRIDE_MODULES.
"""
from django.db.models import Count, Q
from oscar.core.loading import get_class, get_model
from oscarapi.views import product as core_views
from rest_framework.pagination import PageNumberPagination

from apps.api.mobile_serializers import (
    MobileCategorySerializer,
    MobileProductSerializer,
)

Selector = get_class("partner.strategy", "Selector")
Category = get_model("catalogue", "Category")
Product = get_model("catalogue", "Product")
ProductReview = get_model("reviews", "ProductReview")


def with_reviews_count(queryset):
    """Number of approved reviews, read by MobileProductSerializer"""
    return queryset.annotate(
        reviews_count=Count(
            "reviews",
            filter=Q(reviews__status=ProductReview.APPROVED),
            distinct=True,
        )
    )


class MobileStrategyMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        request = self.request
        context["strategy"] = Selector().strategy(request=request, user=request.user)
        return context


class MobileProductPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductList(MobileStrategyMixin, core_views.ProductList):
    """
    Browsable products with price and availability inlined, newest first,
    paginated with ``?page=`` and ``?page_size=``.

    Supports ``?category=<id>`` (the category and its descendants) and
    ``?q=<words>`` (every word in the title, the description or the UPC) on
    top of the core ``?structure=`` filter.
    """

    queryset = with_reviews_count(
        Product.objects.browsable()
        .prefetch_related("images", "categories", "stockrecords")
        .order_by("-date_created", "-id")
    )
    serializer_class = MobileProductSerializer
    pagination_class = MobileProductPagination

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
        return search_products(qs, self.request.query_params.get("q", ""))


def search_products(queryset, query):
    """Products matching every word of ``query`` (no filter when blank)"""
    for word in query.split():
        queryset = queryset.filter(
            Q(title__icontains=word)
            | Q(description__icontains=word)
            | Q(upc__iexact=word)
        )
    return queryset


class ProductDetail(MobileStrategyMixin, core_views.ProductDetail):
    queryset = with_reviews_count(Product.objects.browsable())
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
